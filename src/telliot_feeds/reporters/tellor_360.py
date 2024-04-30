import asyncio
import math
import time
from datetime import timedelta
from typing import Any
from typing import Dict
from typing import Optional
from typing import Tuple
from typing import Union

from eth_abi.exceptions import EncodingTypeError
from eth_utils import to_checksum_address
from telliot_core.contract.contract import Contract
from telliot_core.utils.key_helpers import lazy_unlock_account
from telliot_core.utils.response import error_status
from telliot_core.utils.response import ResponseStatus
from web3.contract import ContractFunction
from web3.types import TxParams
from web3.types import TxReceipt

from telliot_feeds.constants import CHAINS_WITH_TBR
from telliot_feeds.feeds import DataFeed
from telliot_feeds.feeds.trb_usd_feed import trb_usd_median_feed
from telliot_feeds.reporters.rewards.time_based_rewards import get_time_based_rewards
from telliot_feeds.reporters.stake import Stake
from telliot_feeds.reporters.tips.suggest_datafeed import get_feed_and_tip
from telliot_feeds.reporters.tips.tip_amount import fetch_feed_tip
from telliot_feeds.reporters.types import GasParams
from telliot_feeds.reporters.types import StakerInfo
from telliot_feeds.utils.log import get_logger
from telliot_feeds.utils.reporter_utils import get_native_token_feed
from telliot_feeds.utils.reporter_utils import has_native_token_funds
from telliot_feeds.utils.reporter_utils import is_online
from telliot_feeds.utils.reporter_utils import suggest_random_feed
from telliot_feeds.utils.reporter_utils import tkn_symbol
from telliot_feeds.utils.stake_info import StakeInfo

logger = get_logger(__name__)


class Tellor360Reporter(Stake):
    """Reports values from given datafeeds to a TellorFlex."""

    def __init__(
        self,
        autopay: Contract,
        chain_id: int,
        datafeed: Optional[DataFeed[Any]] = None,
        expected_profit: Union[str, float] = "YOLO",
        wait_period: int = 7,
        check_rewards: bool = True,
        ignore_tbr: bool = False,  # relevant only for eth-mainnet and eth-testnets
        stake: float = 0,
        use_random_feeds: bool = False,
        skip_manual_feeds: bool = False,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.autopay = autopay
        self.datafeed = datafeed
        self.skip_manual_feeds = skip_manual_feeds
        self.use_random_feeds: bool = use_random_feeds
        self.qtag_selected = False if self.datafeed is None else True
        self.expected_profit = expected_profit
        self.stake: float = self.from_ether(stake)
        self.stake_info = StakeInfo()
        self.check_rewards: bool = check_rewards
        self.autopaytip = 0
        self.ignore_tbr = ignore_tbr
        self.wait_period = wait_period
        self.chain_id = chain_id
        self.acct_addr = to_checksum_address(self.account.address)
        logger.info(f"Reporting with account: {self.acct_addr}")

    async def get_stake_amount(self) -> Tuple[Optional[int], ResponseStatus]:
        """Reads the current stake amount from the oracle contract

        Returns:
        - (int, ResponseStatus) the current stake amount in TellorFlex
        """
        stake_amount: int
        stake_amount, status = await self.oracle.read("getStakeAmount")
        if not status.ok:
            msg = f"Unable to read current stake amount: {status.error}"
            return None, error_status(msg, status.e, log=logger.error)
        return stake_amount, status

    async def get_staker_details(self) -> Tuple[Optional[StakerInfo], ResponseStatus]:
        """Reads the staker details for the account from the oracle contract

        Returns:
        - (StakerInfo, ResponseStatus) the staker details for the account
        """
        response, status = await self.oracle.read("getStakerInfo", _stakerAddress=self.acct_addr)
        if not status.ok:
            msg = f"Unable to read account staker info: {status.error}"
            return None, error_status(msg, status.e, log=logger.error)
        staker_details = StakerInfo(*response)
        return staker_details, status

    async def ensure_staked(self) -> Tuple[bool, ResponseStatus]:
        """Compares stakeAmount and stakerInfo every loop to monitor changes to the stakeAmount or stakerInfo
        and deposits stake if needed for continuous reporting

        Return:
        - (bool, ResponseStatus)
        """
        # get oracle required stake amount
        stake_amount, status = await self.get_stake_amount()
        if not status.ok or stake_amount is None:
            return False, status
        # store stake amount
        self.stake_info.store_stake_amount(stake_amount)
        # check if stake amount changed (logs when it does)
        self.stake_info.stake_amount_change()

        # get accounts current stake total
        staker_details, status = await self.get_staker_details()
        if not status.ok or staker_details is None:
            return False, status
        # store staker balance
        self.stake_info.store_staker_balance(staker_details.stake_balance)
        # update time of last report
        self.stake_info.update_last_report_time(staker_details.last_report)
        # update reports count
        self.stake_info.update_reports_count(staker_details.reports_count)
        # check if staker balance changed which means a value they submitted has been disputed
        # (logs when it does)
        self.stake_info.is_in_dispute()

        logger.info(
            f"""

            STAKER INFO
            start date: {staker_details.start_date}
            stake_balance: {self.to_ether(staker_details.stake_balance)!r}
            locked_balance: {staker_details.locked_balance}
            last report: {staker_details.last_report}
            reports count: {staker_details.reports_count}
            """
        )

        # deposit stake if stakeAmount in oracle is greater than account stake or
        # a stake in cli is selected thats greater than account stake
        chosen_stake_amount = self.stake > staker_details.stake_balance
        if chosen_stake_amount:
            logger.info("Chosen stake is greater than account stake balance")
        if self.stake_info.stake_amount_gt_staker_balance or chosen_stake_amount:
            logger.info("Approving and depositing stake...")
            # amount to deposit whichever largest difference either chosen stake or stakeAmount to keep reporting
            # current oracle stake amount vs current account stake balance
            to_stake_amount_1 = self.stake_info.current_stake_amount - staker_details.stake_balance
            # chosen stake via cli flag vs current account stake balance
            to_stake_amount_2 = self.stake - staker_details.stake_balance
            amount_to_stake = max(int(to_stake_amount_1), int(to_stake_amount_2))

            _, deposit_status = await self.deposit_stake(amount_to_stake)
            if not deposit_status.ok:
                return False, deposit_status

            # add staked balance after successful stake deposit
            self.stake_info.update_staker_balance(amount_to_stake)

        return True, ResponseStatus()

    async def check_reporter_lock(self) -> ResponseStatus:
        """Checks reporter lock time to determine when reporting is allowed

        Return:
        - ResponseStatus: yay or nay
        """
        staker_balance = self.stake_info.current_staker_balance
        current_stake_amount = self.stake_info.current_stake_amount
        if staker_balance is None or current_stake_amount is None:
            msg = "Unable to calculate reporter lock remaining time"
            return error_status(msg, log=logger.info)

        # 12hrs in seconds is 43200
        try:
            reporter_lock = 43200 / math.floor(staker_balance / current_stake_amount)
        except ZeroDivisionError:  # Tellor Playground contract's stakeAmount is 0
            reporter_lock = 0
        time_remaining = round(self.stake_info.last_report_time + reporter_lock - time.time())
        if time_remaining > 0:
            hr_min_sec = str(timedelta(seconds=time_remaining))
            msg = "Currently in reporter lock. Time left: " + hr_min_sec
            return error_status(msg, log=logger.info)

        return ResponseStatus()

    async def rewards(self) -> int:
        """Fetches total time based rewards plus tips for current datafeed"""
        if self.datafeed is not None:
            try:
                datafeed = self.datafeed
                self.autopaytip += await fetch_feed_tip(self.autopay, datafeed)
            except EncodingTypeError:
                logger.warning(f"Unable to generate data/id for query: {self.datafeed.query}")
        if self.ignore_tbr:
            logger.info("Ignoring time based rewards")
            return self.autopaytip
        elif self.chain_id in CHAINS_WITH_TBR:
            logger.info("Fetching time based rewards")
            time_based_rewards = await get_time_based_rewards(self.oracle)
            logger.info(f"Time based rewards: {self.to_ether(time_based_rewards):.04f}")
            if time_based_rewards is not None:
                self.autopaytip += time_based_rewards
        return self.autopaytip

    async def fetch_datafeed(self) -> Optional[DataFeed[Any]]:
        """Fetches datafeed

        If the user did not select a query tag, there will have been no datafeed passed to
        the reporter upon instantiation.
        If the user uses the random feeds flag, the datafeed will be chosen randomly.
        If the user did not select a query tag or use the random feeds flag, the datafeed will
        be chosen based on the most funded datafeed in the AutoPay contract.

        If the no-rewards-check flag is used, the reporter will not check profitability or
        available tips for the datafeed unless the user has not selected a query tag or
        used the random feeds flag.
        """
        # reset autopay tip every time fetch_datafeed is called
        # so that tip is checked fresh every time and not carry older tips
        self.autopaytip = 0
        # TODO: This should be removed and moved to profit check method perhaps
        if self.check_rewards:
            # calculate tbr and
            _ = await self.rewards()

        if self.use_random_feeds:
            self.datafeed = suggest_random_feed()

        # Fetch datafeed based on whichever is most funded in the AutoPay contract
        if self.datafeed is None:
            suggested_feed, tip_amount = await get_feed_and_tip(self.autopay, self.skip_manual_feeds)

            if suggested_feed is not None and tip_amount is not None:
                logger.info(f"Most funded datafeed in Autopay: {suggested_feed.query.type}")
                logger.info(f"Tip amount: {self.to_ether(tip_amount)}")
                self.autopaytip += tip_amount

                self.datafeed = suggested_feed
                return self.datafeed

        return self.datafeed

    async def ensure_profitable(self) -> ResponseStatus:

        status = ResponseStatus()
        if not self.check_rewards:
            return status

        tip = self.to_ether(self.autopaytip)
        # Fetch token prices in USD
        native_token_feed = get_native_token_feed(self.chain_id)
        price_feeds = [native_token_feed, trb_usd_median_feed]
        _ = await asyncio.gather(*[feed.source.fetch_new_datapoint() for feed in price_feeds])
        price_native_token = native_token_feed.source.latest[0]
        price_trb_usd = trb_usd_median_feed.source.latest[0]

        if price_native_token is None or price_trb_usd is None:
            return error_status("Unable to fetch token price", log=logger.warning)

        gas_info = self.get_gas_info_core()
        max_fee_per_gas = gas_info["max_fee_per_gas"]
        legacy_gas_price = gas_info["legacy_gas_price"]
        gas_limit = gas_info["gas_limit"]

        max_gas = max_fee_per_gas if max_fee_per_gas else legacy_gas_price
        # multiply gasPrice by gasLimit
        if max_gas is None or gas_limit is None:
            return error_status("Unable to calculate profitablity, no gas fees set", log=logger.warning)

        txn_fee = max_gas * self.to_gwei(int(gas_limit))
        logger.info(
            f"""\n
            Tips: {tip}
            Transaction fee: {txn_fee} {tkn_symbol(self.chain_id)}
            Gas limit: {gas_limit}
            Gas price: {legacy_gas_price} gwei
            Max fee per gas: {max_fee_per_gas} gwei
            Max priority fee per gas: {gas_info["max_priority_fee_per_gas"]} gwei
            Txn type: {self.transaction_type}\n"""
        )

        # Calculate profit
        rev_usd = tip * price_trb_usd
        costs_usd = txn_fee * price_native_token  # convert gwei costs to eth, then to usd
        profit_usd = rev_usd - costs_usd
        logger.info(f"Estimated profit: ${round(profit_usd, 2)}")
        logger.info(f"tip price: {round(rev_usd, 2)}, gas costs: {costs_usd}")

        percent_profit = ((profit_usd) / costs_usd) * 100
        logger.info(f"Estimated percent profit: {round(percent_profit, 2)}%")
        if (self.expected_profit != "YOLO") and (
            isinstance(self.expected_profit, float) and percent_profit < self.expected_profit
        ):
            status.ok = False
            status.error = "Estimated profitability below threshold."
            logger.info(status.error)
            return status
        # reset autopay tip to check for tips again
        self.autopaytip = 0

        return status

    async def get_num_reports_by_id(self, query_id: bytes) -> Tuple[int, ResponseStatus]:
        count, read_status = await self.oracle.read(func_name="getNewValueCountbyQueryId", _queryId=query_id)
        return count, read_status

    async def submission_txn_params(self, datafeed: DataFeed[Any]) -> Tuple[Optional[Dict[str, Any]], ResponseStatus]:
        """Assemble the submitValue transaction
        Params:
            datafeed: The datafeed object

        Returns a tuple of the web3 function object and a ResponseStatus object
        """
        # Update datafeed value
        await datafeed.source.fetch_new_datapoint()
        latest_data = datafeed.source.latest
        if latest_data[0] is None:
            msg = "Unable to retrieve updated datafeed value."
            return None, error_status(msg, log=logger.info)
        # Get query info & encode value to bytes
        query_id = datafeed.query.query_id
        query_data = datafeed.query.query_data
        try:
            value = datafeed.query.value_type.encode(latest_data[0])
            logger.debug(f"Current query: {datafeed.query.descriptor}")
            logger.debug(f"Reporter Encoded value: {value.hex()}")
        except Exception as e:
            msg = f"Error encoding response value {latest_data[0]}"
            return None, error_status(msg, e=e, log=logger.error)

        # Get nonce
        report_count, read_status = await self.get_num_reports_by_id(query_id)
        if not read_status.ok:
            msg = f"Unable to retrieve report count for query id: {read_status.error}"
            return None, error_status(msg, read_status.e, logger.error)

        params = {"_queryId": query_id, "_value": value, "_nonce": report_count, "_queryData": query_data}
        return params, ResponseStatus()

    def assemble_function(
        self, function_name: str, **transaction_params: Any
    ) -> Tuple[Optional[ContractFunction], ResponseStatus]:
        """Assemble a contract function"""
        try:
            func = self.oracle.contract.get_function_by_name(function_name)(**transaction_params)
            return func, ResponseStatus()
        except Exception as e:
            return None, error_status("Error assembling function", e, logger.error)

    def build_transaction(
        self, function_name: str, **transaction_params: Any
    ) -> Tuple[Optional[TxParams], ResponseStatus]:
        """Build a transaction"""

        contract_function, status = self.assemble_function(function_name=function_name, **transaction_params)
        if contract_function is None:
            return None, error_status("Error building function to estimate gas", status.e, logger.error)

        # set gas parameters globally
        status = self.update_gas_fees()
        logger.debug(status)
        if not status.ok:
            return None, error_status("Error setting gas parameters", status.e, logger.error)

        _, status = self.estimate_gas_amount(contract_function)
        if not status.ok:
            return None, error_status(f"Error estimating gas for function: {contract_function}", status.e, logger.error)

        params, status = self.tx_params(**self.get_gas_info())
        logger.debug(f"Transaction parameters: {params}")
        if params is None:
            return None, error_status("Error getting transaction parameters", status.e, logger.error)

        return contract_function.buildTransaction(params), ResponseStatus()  # type: ignore

    def sign_n_send_transaction(self, built_tx: Any) -> Tuple[Optional[TxReceipt], ResponseStatus]:
        """Send a signed transaction to the blockchain and wait for confirmation

        Params:
            tx_signed: The signed transaction object

        Returns a tuple of the transaction receipt and a ResponseStatus object
        """
        lazy_unlock_account(self.account)
        local_account = self.account.local_account
        tx_signed = local_account.sign_transaction(built_tx)
        try:
            tx_hash = self.web3.eth.send_raw_transaction(tx_signed.rawTransaction)
        except Exception as e:
            note = "Send transaction failed"
            return None, error_status(note, log=logger.error, e=e)

        try:
            # Confirm transaction
            tx_receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash, timeout=360)

            tx_url = f"{self.endpoint.explorer}/tx/{tx_hash.hex()}"

            if tx_receipt["status"] == 0:
                msg = f"Transaction reverted. ({tx_url})"
                return tx_receipt, error_status(msg, log=logger.error)

            logger.info(f"View reported data: \n{tx_url}")
            return tx_receipt, ResponseStatus()
        except Exception as e:
            note = "Failed to confirm transaction"
            return None, error_status(note, log=logger.error, e=e)

    def get_acct_nonce(self) -> Tuple[Optional[int], ResponseStatus]:
        """Get the nonce for the account"""
        try:
            return self.web3.eth.get_transaction_count(self.acct_address), ResponseStatus()
        except ValueError as e:
            return None, error_status("Account nonce request timed out", e=e, log=logger.warning)
        except Exception as e:
            return None, error_status("Unable to retrieve account nonce", e=e, log=logger.error)

    def tx_params(self, **gas_fees: GasParams) -> Tuple[Optional[Dict[str, Any]], ResponseStatus]:
        """Return transaction parameters"""
        nonce, status = self.get_acct_nonce()
        if nonce is None:
            return None, status
        return {
            "nonce": nonce,
            "chainId": self.chain_id,
            **gas_fees,
        }, ResponseStatus()

    def has_native_token(self) -> bool:
        """Check if account has native token funds for a network for gas fees
        of at least min_native_token_balance that is set in the cli"""
        return has_native_token_funds(self.acct_addr, self.web3, min_balance=self.min_native_token_balance)

    async def report_once(
        self,
    ) -> Tuple[Optional[TxReceipt], ResponseStatus]:
        """Report query value once
        This method checks to see if a user is able to submit
        values to the oracle, given their staker status
        and last submission time. Also, this method does not
        submit values if doing so won't make a profit."""
        # Check staker status
        staked, status = await self.ensure_staked()
        if not staked or not status.ok:
            return None, status

        status = await self.check_reporter_lock()
        if not status.ok:
            return None, status

        # Get suggested datafeed if none provided
        datafeed = await self.fetch_datafeed()
        if not datafeed:
            msg = "Unable to suggest datafeed"
            return None, error_status(note=msg, log=logger.info)

        params, status = await self.submission_txn_params(datafeed)
        if not status.ok or params is None:
            return None, status

        build_tx, status = self.build_transaction("submitValue", **params)
        if not status.ok or build_tx is None:
            return None, status

        # Check if profitable if not YOLO
        status = await self.ensure_profitable()
        logger.debug(f"Ensure profitibility method status: {status}")
        if not status.ok:
            return None, status

        logger.debug("Sending submitValue transaction")
        tx_receipt, status = self.sign_n_send_transaction(build_tx)
        # reset datafeed for a new suggestion if qtag wasn't selected in cli
        if self.qtag_selected is False:
            self.datafeed = None

        return tx_receipt, status

    async def is_online(self) -> bool:
        return await is_online()

    async def report(self, report_count: Optional[int] = None) -> None:
        """Submit values to Tellor oracles on an interval."""

        while report_count is None or report_count > 0:
            if await self.is_online():
                if self.has_native_token():
                    _, _ = await self.report_once()
            else:
                logger.warning("Unable to connect to the internet!")

            logger.info(f"Sleeping for {self.wait_period} seconds")
            await asyncio.sleep(self.wait_period)

            if report_count is not None:
                report_count -= 1
