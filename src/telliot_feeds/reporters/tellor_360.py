import asyncio
import math
import time
from dataclasses import dataclass
from datetime import timedelta
from typing import Any
from typing import Optional
from typing import Tuple
from typing import Union

from chained_accounts import ChainedAccount
from eth_abi.exceptions import EncodingTypeError
from eth_utils import to_checksum_address
from telliot_core.contract.contract import Contract
from telliot_core.model.endpoints import RPCEndpoint
from telliot_core.utils.key_helpers import lazy_unlock_account
from telliot_core.utils.response import error_status
from telliot_core.utils.response import ResponseStatus
from web3 import Web3
from web3.contract import ContractFunction
from web3.types import TxReceipt

from telliot_feeds.constants import CHAINS_WITH_TBR
from telliot_feeds.feeds import DataFeed
from telliot_feeds.feeds.trb_usd_feed import trb_usd_median_feed
from telliot_feeds.reporters.rewards.time_based_rewards import get_time_based_rewards
from telliot_feeds.reporters.tips.suggest_datafeed import get_feed_and_tip
from telliot_feeds.reporters.tips.tip_amount import fetch_feed_tip
from telliot_feeds.utils.log import get_logger
from telliot_feeds.utils.reporter_utils import fee_history_priority_fee_estimate
from telliot_feeds.utils.reporter_utils import get_native_token_feed
from telliot_feeds.utils.reporter_utils import has_native_token_funds
from telliot_feeds.utils.reporter_utils import is_online
from telliot_feeds.utils.reporter_utils import suggest_random_feed
from telliot_feeds.utils.reporter_utils import tkn_symbol
from telliot_feeds.utils.stake_info import StakeInfo

logger = get_logger(__name__)


@dataclass
class StakerInfo:
    """Data types for staker info
    start_date: TimeStamp
    stake_balance: int
    locked_balance: int
    reward_debt: int
    last_report: TimeStamp
    reports_count: int
    gov_vote_count: int
    vote_count: int
    in_total_stakers: bool
    """

    start_date: int
    stake_balance: int
    locked_balance: int
    reward_debt: int
    last_report: int
    reports_count: int
    gov_vote_count: int
    vote_count: int
    in_total_stakers: bool


@dataclass
class GasParams:
    priority_fee: Optional[float] = None
    max_fee: Optional[float] = None
    gas_price_in_gwei: Union[float, int, None] = None


class Tellor360Reporter:
    """Reports values from given datafeeds to a TellorFlex."""

    def __init__(
        self,
        endpoint: RPCEndpoint,
        account: ChainedAccount,
        chain_id: int,
        oracle: Contract,
        token: Contract,
        autopay: Contract,
        datafeed: Optional[DataFeed[Any]] = None,
        expected_profit: Union[str, float] = "YOLO",
        transaction_type: int = 2,
        gas_limit: Optional[int] = None,
        max_fee: int = 0,
        priority_fee: float = 0.0,
        legacy_gas_price: Optional[int] = None,
        gas_multiplier: int = 1,  # 1 percent
        max_priority_fee_range: int = 80,  # 80 gwei
        wait_period: int = 7,
        min_native_token_balance: int = 10**18,
        check_rewards: bool = True,
        ignore_tbr: bool = False,  # relevant only for eth-mainnet and eth-testnets
        stake: float = 0,
        use_random_feeds: bool = False,
    ) -> None:
        self.endpoint = endpoint
        self.account = account
        self.chain_id = chain_id
        self.oracle = oracle
        self.token = token
        self.autopay = autopay
        # datafeed stuff
        self.datafeed = datafeed
        self.use_random_feeds: bool = use_random_feeds
        self.qtag_selected = False if self.datafeed is None else True
        # profitibility stuff
        self.expected_profit = expected_profit
        # stake amount stuff
        self.stake: float = stake
        self.stake_info = StakeInfo()

        self.min_native_token_balance = min_native_token_balance
        # check rewards bool flag
        self.check_rewards: bool = check_rewards
        self.autopaytip = 0
        self.web3: Web3 = self.endpoint.web3
        # ignore tbr bool flag to optionally disregard time based rewards
        self.ignore_tbr = ignore_tbr
        self.last_submission_timestamp = 0
        # gas stuff
        self.transaction_type = transaction_type
        self.gas_limit = gas_limit
        self.max_fee = max_fee
        self.wait_period = wait_period
        self.priority_fee = priority_fee
        self.legacy_gas_price = legacy_gas_price
        self.gas_multiplier = gas_multiplier
        self.max_priority_fee_range = max_priority_fee_range
        self.gas_info: dict[str, Union[float, int]] = {}

        self.acct_addr = to_checksum_address(account.address)
        logger.info(f"Reporting with account: {self.acct_addr}")
        # TODO: why is this here?
        # assert self.acct_addr == to_checksum_address(self.account.address)

    async def get_stake_amount(self) -> Tuple[Optional[int], ResponseStatus]:
        """Reads the current stake amount from the oracle contract

        Returns:
        - (int, ResponseStatus) the current stake amount in TellorFlex
        """
        response, status = await self.oracle.read("getStakeAmount")
        if not status.ok:
            msg = f"Unable to read current stake amount: {status.e}"
            return None, error_status(msg, log=logger.error)
        stake_amount: int = response
        return stake_amount, status

    async def get_staker_details(self) -> Tuple[Optional[StakerInfo], ResponseStatus]:
        """Reads the staker details for the account from the oracle contract

        Returns:
        - (StakerInfo, ResponseStatus) the staker details for the account
        """
        response, status = await self.oracle.read("getStakerInfo", _stakerAddress=self.acct_addr)
        if not status.ok:
            msg = f"Unable to read account staker info {status.e}"
            return None, error_status(msg, log=logger.error)
        staker_details = StakerInfo(*response)
        return staker_details, status

    async def get_current_balance(self) -> Tuple[Optional[int], ResponseStatus]:
        """Reads the current balance of the account"""
        response, status = await self.token.read("balanceOf", account=self.acct_addr)
        if not status.ok:
            msg = f"Unable to read account balance: {status.e}"
            return None, error_status(msg, log=logger.error)
        wallet_balance: int = response
        logger.info(f"Current wallet TRB balance: {wallet_balance / 1e18!r}")
        return wallet_balance, status

    async def gas_params(self) -> Tuple[Optional[GasParams], ResponseStatus]:
        """Returns the gas params for the transaction

        Returns:
        - priority_fee: float, the priority fee in gwei
        - max_fee: int, the max fee in wei
        - gas_price_in_gwei: float, the gas price in gwei
        """
        if self.transaction_type == 2:
            priority_fee, max_fee = self.get_fee_info()
            if priority_fee is None or max_fee is None:
                return None, error_status("Unable to suggest type 2 txn fees", log=logger.error)
            return GasParams(priority_fee=priority_fee, max_fee=max_fee), ResponseStatus()

        else:
            # Fetch legacy gas price if not provided by user
            if self.legacy_gas_price is None:
                gas_price_in_gwei = await self.fetch_gas_price()
                if not gas_price_in_gwei:
                    note = "Unable to fetch gas price for staking tx type 0"
                    return None, error_status(note, log=logger.warning)
            else:
                gas_price_in_gwei = self.legacy_gas_price
        return GasParams(gas_price_in_gwei=gas_price_in_gwei), ResponseStatus()

    async def deposit_stake(self, amount: int) -> Tuple[bool, ResponseStatus]:
        """Deposits stake into the oracle contract"""
        # check allowance to avoid unnecessary approval transactions
        allowance, allowance_status = await self.token.read(
            "allowance", owner=self.acct_addr, spender=self.oracle.address
        )
        if not allowance_status.ok:
            msg = f"Unable to check allowance: {allowance_status.e}"
            return False, error_status(msg, log=logger.error)
        logger.debug(f"Current allowance: {allowance / 1e18!r}")
        gas_params, status = await self.gas_params()
        if not status.ok or not gas_params:
            return False, status
        # if allowance is less than amount_to_stake then approve
        if allowance < amount:
            # Approve token spending
            logger.info("Approving token spending")
            approve_receipt, approve_status = await self.token.write(
                func_name="approve",
                gas_limit=self.gas_limit,
                max_priority_fee_per_gas=gas_params.priority_fee,
                max_fee_per_gas=gas_params.max_fee,
                legacy_gas_price=gas_params.gas_price_in_gwei,
                spender=self.oracle.address,
                amount=amount,
            )
            if not approve_status.ok:
                msg = f"Unable to approve staking: {approve_status.e}"
                return False, error_status(msg, log=logger.error)
            logger.debug(f"Approve transaction status: {approve_receipt.status}, block: {approve_receipt.blockNumber}")
            # Add this to avoid nonce error from txn happening too fast
            time.sleep(1)

        # deposit stake
        logger.info("Depositing stake")
        deposit_receipt, deposit_status = await self.oracle.write(
            func_name="depositStake",
            gas_limit=self.gas_limit,
            max_priority_fee_per_gas=gas_params.priority_fee,
            max_fee_per_gas=gas_params.max_fee,
            legacy_gas_price=gas_params.gas_price_in_gwei,
            _amount=amount,
        )
        if not deposit_status.ok:
            msg = f"Unable to deposit stake: {deposit_status.e}"
            return False, error_status(msg, log=logger.error)
        logger.debug(f"Deposit transaction status: {deposit_receipt.status}, block: {deposit_receipt.blockNumber}")
        return True, deposit_status

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
            stake_balance: {staker_details.stake_balance / 1e18!r}
            locked_balance: {staker_details.locked_balance}
            last report: {staker_details.last_report}
            reports count: {staker_details.reports_count}
            """
        )

        # deposit stake if stakeAmount in oracle is greater than account stake or
        # a stake in cli is selected thats greater than account stake
        chosen_stake_amount = (self.stake * 1e18) > staker_details.stake_balance
        if chosen_stake_amount:
            logger.info("Chosen stake is greater than account stake balance")
        if self.stake_info.stake_amount_gt_staker_balance or chosen_stake_amount:
            logger.info("Approving and depositing stake...")
            # amount to deposit whichever largest difference either chosen stake or stakeAmount to keep reporting
            # current oracle stake amount vs current account stake balance
            to_stake_amount_1 = self.stake_info.current_stake_amount - staker_details.stake_balance
            # chosen stake via cli flag vs current account stake balance
            to_stake_amount_2 = (self.stake * 1e18) - staker_details.stake_balance
            amount_to_stake = max(int(to_stake_amount_1), int(to_stake_amount_2))

            # check TRB wallet balance!
            wallet_balance, wallet_balance_status = await self.get_current_balance()
            if not wallet_balance or not wallet_balance_status.ok:
                return False, wallet_balance_status

            if amount_to_stake > wallet_balance:
                msg = (
                    f"Amount to stake: {amount_to_stake/1e18:.04f} "
                    f"is greater than your balance: {wallet_balance/1e18:.04f} so "
                    "not enough TRB to cover the stake"
                )
                return False, error_status(msg, log=logger.warning)

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
            logger.info(f"Time based rewards: {time_based_rewards/1e18:.04f}")
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
            suggested_feed, tip_amount = await get_feed_and_tip(self.autopay)

            if suggested_feed is not None and tip_amount is not None:
                logger.info(f"Most funded datafeed in Autopay: {suggested_feed.query.type}")
                logger.info(f"Tip amount: {tip_amount/1e18}")
                self.autopaytip += tip_amount

                self.datafeed = suggested_feed
                return self.datafeed

        return self.datafeed

    async def fetch_gas_price(self) -> Optional[float]:
        """Fetches the current gas price from an EVM network and returns
        an adjusted gas price.

        Returns:
            An optional integer representing the adjusted gas price in wei, or
            None if the gas price could not be retrieved.
        """
        try:
            price = self.web3.eth.gas_price
            price_gwei = self.web3.fromWei(price, "gwei")
        except Exception as e:
            logger.error(f"Error fetching gas price: {e}")
            return None
        # increase gas price by 1.0 + gas_multiplier
        multiplier = 1.0 + (self.gas_multiplier / 100.0)
        gas_price = (float(price_gwei) * multiplier) if price_gwei else None
        return gas_price

    def get_fee_info(self) -> Tuple[Optional[float], Optional[int]]:
        """Calculate max fee and priority fee if not set
        for more info:
            https://web3py.readthedocs.io/en/v5/web3.eth.html?highlight=fee%20history#web3.eth.Eth.fee_history
        """
        if self.max_fee is None:
            try:
                fee_history = self.web3.eth.fee_history(
                    block_count=5, newest_block="latest", reward_percentiles=[25, 50, 75]
                )
                # "base fee for the next block after the newest of the returned range"
                base_fee = fee_history.baseFeePerGas[-1] / 1e9
                # estimate priority fee from fee history
                priority_fee_max = int(self.max_priority_fee_range * 1e9)  # convert to wei
                priority_fee = fee_history_priority_fee_estimate(fee_history, priority_fee_max=priority_fee_max) / 1e9
                max_fee = base_fee + priority_fee
                return priority_fee, max_fee
            except Exception as e:
                logger.warning(f"Error in calculating gas fees: {e}")
                return None, None
        return self.priority_fee, self.max_fee

    async def get_num_reports_by_id(self, query_id: bytes) -> Tuple[int, ResponseStatus]:
        count, read_status = await self.oracle.read(func_name="getNewValueCountbyQueryId", _queryId=query_id)
        return count, read_status

    def has_native_token(self) -> bool:
        """Check if account has native token funds for a network for gas fees
        of at least min_native_token_balance that is set in the cli"""
        return has_native_token_funds(self.acct_addr, self.web3, min_balance=self.min_native_token_balance)

    async def ensure_profitable(self) -> ResponseStatus:

        status = ResponseStatus()
        if not self.check_rewards:
            return status

        tip = self.autopaytip
        # Fetch token prices in USD
        native_token_feed = get_native_token_feed(self.chain_id)
        price_feeds = [native_token_feed, trb_usd_median_feed]
        _ = await asyncio.gather(*[feed.source.fetch_new_datapoint() for feed in price_feeds])
        price_native_token = native_token_feed.source.latest[0]
        price_trb_usd = trb_usd_median_feed.source.latest[0]

        if price_native_token is None or price_trb_usd is None:
            return error_status("Unable to fetch token price", log=logger.warning)

        if not self.gas_info:
            return error_status("Gas info not set", log=logger.warning)

        gas_info = self.gas_info

        if gas_info["type"] == 0:
            txn_fee = int(gas_info["gas_price"] * gas_info["gas_limit"])
            logger.info(
                f"""

                Tips: {tip/1e18}
                Transaction fee: {self.web3.fromWei(txn_fee, 'gwei'):.09f} {tkn_symbol(self.chain_id)}
                Gas price: {gas_info["gas_price"]} gwei
                Gas limit: {gas_info["gas_limit"]}
                Txn type: 0 (Legacy)
                """
            )
        if gas_info["type"] == 2:
            txn_fee = int(gas_info["max_fee"] * gas_info["gas_limit"])
            logger.info(
                f"""

                Tips: {tip/1e18}
                Max transaction fee: {self.web3.fromWei(txn_fee, 'gwei'):.18f} {tkn_symbol(self.chain_id)}
                Max fee per gas: {gas_info["max_fee"]} gwei
                Max priority fee per gas: {gas_info["priority_fee"]} gwei
                Gas limit: {gas_info["gas_limit"]}
                Txn type: 2 (EIP-1559)
                """
            )

        # Calculate profit
        rev_usd = tip / 1e18 * price_trb_usd
        costs_usd = txn_fee / 1e9 * price_native_token  # convert gwei costs to eth, then to usd
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
            # reset datafeed for a new suggestion if qtag wasn't selected in cli
            if self.qtag_selected is False:
                self.datafeed = None
            return status
        # reset autopay tip to check for tips again
        self.autopaytip = 0
        # reset datafeed for a new suggestion if qtag wasn't selected in cli
        if self.qtag_selected is False:
            self.datafeed = None

        return status

    def get_acct_nonce(self) -> Tuple[Optional[int], ResponseStatus]:
        """Get transaction count for an address"""
        try:
            return self.web3.eth.get_transaction_count(self.acct_addr), ResponseStatus()
        except ValueError as e:
            return None, error_status("Account nonce request timed out", e=e, log=logger.warning)
        except Exception as e:
            return None, error_status("Unable to retrieve account nonce", e=e, log=logger.error)

    def submit_val_tx_gas_limit(self, submit_val_tx: ContractFunction) -> Tuple[Optional[int], ResponseStatus]:
        """Estimate gas usage for submitValue transaction
        Args:
            submit_val_tx: The submitValue transaction object
        Returns a tuple of the gas limit and a ResponseStatus object"""
        if self.gas_limit is None:
            try:
                gas_limit: int = submit_val_tx.estimateGas({"from": self.acct_addr})
                if not gas_limit:
                    return None, error_status("Unable to estimate gas for submitValue transaction")
                return gas_limit, ResponseStatus()
            except Exception as e:
                msg = "Unable to estimate gas for submitValue transaction"
                return None, error_status(msg, e=e, log=logger.error)
        return self.gas_limit, ResponseStatus()

    async def assemble_submission_txn(
        self, datafeed: DataFeed[Any]
    ) -> Tuple[Optional[ContractFunction], ResponseStatus]:
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
        query = datafeed.query
        query_id = query.query_id
        query_data = query.query_data
        try:
            value = query.value_type.encode(latest_data[0])
            logger.debug(f"IntervalReporter Encoded value: {value.hex()}")
        except Exception as e:
            msg = f"Error encoding response value {latest_data[0]}"
            return None, error_status(msg, e=e, log=logger.error)

        # Get nonce
        report_count, read_status = await self.get_num_reports_by_id(query_id)

        if not read_status.ok:
            read_status.error = (
                "Unable to retrieve report count: " + read_status.error
            )  # error won't be none # noqa: E501
            logger.error(read_status.error)
            read_status.e = read_status.e
            return None, read_status

        # Start transaction build
        submit_val_func = self.oracle.contract.get_function_by_name("submitValue")
        params: ContractFunction = submit_val_func(
            _queryId=query_id,
            _value=value,
            _nonce=report_count,
            _queryData=query_data,
        )
        return params, ResponseStatus()

    def send_transaction(self, tx_signed: Any) -> Tuple[Optional[TxReceipt], ResponseStatus]:
        """Send a signed transaction to the blockchain and wait for confirmation

        Params:
            tx_signed: The signed transaction object

        Returns a tuple of the transaction receipt and a ResponseStatus object
        """
        try:
            logger.debug("Sending submitValue transaction")
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

        logger.info(f"Current query: {datafeed.query.descriptor}")

        submit_val_tx, status = await self.assemble_submission_txn(datafeed)
        if not status.ok or submit_val_tx is None:
            return None, status

        # Get account nonce
        acc_nonce, nonce_status = self.get_acct_nonce()
        if not nonce_status.ok:
            return None, nonce_status

        gas_params, status = await self.gas_params()
        if gas_params is None or not status.ok:
            return None, status

        # Estimate gas usage amount
        gas_limit, status = self.submit_val_tx_gas_limit(submit_val_tx=submit_val_tx)
        if not status.ok or gas_limit is None:
            return None, status

        self.gas_info["gas_limit"] = gas_limit
        if gas_params.max_fee is not None and gas_params.priority_fee is not None:
            self.gas_info["type"] = 2
            self.gas_info["max_fee"] = gas_params.max_fee
            self.gas_info["priority_fee"] = gas_params.priority_fee
            self.gas_info["base_fee"] = gas_params.max_fee - gas_params.priority_fee
            gas_fees = {
                "maxPriorityFeePerGas": self.web3.toWei(gas_params.priority_fee, "gwei"),
                "maxFeePerGas": self.web3.toWei(gas_params.max_fee, "gwei"),
            }

        if gas_params.gas_price_in_gwei is not None:
            self.gas_info["type"] = 0
            self.gas_info["gas_price"] = gas_params.gas_price_in_gwei
            gas_fees = {"gasPrice": self.web3.toWei(gas_params.gas_price_in_gwei, "gwei")}

        # Check if profitable if not YOLO
        status = await self.ensure_profitable()
        if not status.ok:
            return None, status

        # Build transaction
        built_submit_val_tx = submit_val_tx.buildTransaction(
            dict(nonce=acc_nonce, gas=gas_limit, chainId=self.chain_id, **gas_fees)  # type: ignore
        )
        lazy_unlock_account(self.account)
        local_account = self.account.local_account
        tx_signed = local_account.sign_transaction(built_submit_val_tx)

        tx_receipt, status = self.send_transaction(tx_signed)

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
