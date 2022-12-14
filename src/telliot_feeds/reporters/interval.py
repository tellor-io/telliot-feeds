""" BTCUSD Price Reporter
Example of a subclassed Reporter.
"""
import asyncio
import time
from typing import Any
from typing import Optional
from typing import Tuple
from typing import Union

from chained_accounts import ChainedAccount
from eth_utils import to_checksum_address
from telliot_core.contract.contract import Contract
from telliot_core.gas.legacy_gas import ethgasstation
from telliot_core.model.endpoints import RPCEndpoint
from telliot_core.utils.key_helpers import lazy_unlock_account
from telliot_core.utils.response import error_status
from telliot_core.utils.response import ResponseStatus
from web3 import Web3
from web3.datastructures import AttributeDict

from telliot_feeds.datafeed import DataFeed
from telliot_feeds.feeds import CATALOG_FEEDS
from telliot_feeds.feeds.eth_usd_feed import eth_usd_median_feed
from telliot_feeds.feeds.trb_usd_feed import trb_usd_median_feed
from telliot_feeds.sources.etherscan_gas import EtherscanGasPriceSource
from telliot_feeds.utils.log import get_logger
from telliot_feeds.utils.reporter_utils import has_native_token_funds
from telliot_feeds.utils.reporter_utils import is_online
from telliot_feeds.utils.reporter_utils import tellor_suggested_report


logger = get_logger(__name__)


class IntervalReporter:
    """Reports values from given datafeeds to a TellorX Oracle
    every 7 seconds."""

    def __init__(
        self,
        endpoint: RPCEndpoint,
        account: ChainedAccount,
        chain_id: int,
        master: Contract,
        oracle: Contract,
        datafeed: Optional[DataFeed[Any]] = None,
        expected_profit: Union[str, float] = 100.0,
        transaction_type: int = 0,
        gas_limit: int = 350000,
        max_fee: Optional[int] = None,
        priority_fee: int = 5,
        legacy_gas_price: Optional[int] = None,
        gas_price_speed: str = "fast",
        wait_period: int = 10,
        min_native_token_balance: int = 10**18,
    ) -> None:

        self.endpoint = endpoint
        self.account = account
        self.master = master
        self.oracle = oracle
        self.datafeed = datafeed
        self.chain_id = chain_id
        self.acct_addr = to_checksum_address(account.address)
        self.last_submission_timestamp = 0
        self.expected_profit = expected_profit
        self.transaction_type = transaction_type
        self.gas_limit = gas_limit
        self.max_fee = max_fee
        self.priority_fee = priority_fee
        self.legacy_gas_price = legacy_gas_price
        self.gas_price_speed = gas_price_speed
        self.trb_usd_median_feed = trb_usd_median_feed
        self.eth_usd_median_feed = eth_usd_median_feed
        self.wait_period = wait_period
        self.min_native_token_balance = min_native_token_balance

        logger.info(f"Reporting with account: {self.acct_addr}")

    async def check_reporter_lock(self) -> ResponseStatus:
        """Ensure enough time has passed since last report
        Returns a bool signifying whether a given address is in a
        reporter lock or not (TellorX oracle users cannot submit
        multiple times within 12 hours)."""
        status = ResponseStatus()

        # Save last submission timestamp to reduce web3 calls
        if self.last_submission_timestamp == 0:
            last_timestamp, read_status = await self.oracle.read("getReporterLastTimestamp", _reporter=self.acct_addr)

            # Log web3 errors
            if (not read_status.ok) or (last_timestamp is None):
                status.ok = False
                status.error = "Unable to retrieve reporter's last report timestamp:" + read_status.error
                logger.error(status.error)
                status.e = read_status.e
                return status

            self.last_submission_timestamp = last_timestamp
            logger.info(f"Last submission timestamp: {self.last_submission_timestamp}")

        if time.time() < self.last_submission_timestamp + 43200:  # 12 hours in seconds
            status.ok = False
            status.error = "Current address is in reporter lock."
            logger.info(status.error)
            return status

        return status

    async def fetch_gas_price(self, speed: str = "average") -> Optional[int]:
        """Fetch gas price from ethgasstation in gwei."""
        return await ethgasstation(speed)  # type: ignore

    async def ensure_staked(self) -> Tuple[bool, ResponseStatus]:
        """Make sure the current user is staked
        Returns a bool signifying whether the current address is
        staked. If the address is not initially, it attempts to stake with
        the address's funds."""
        status = ResponseStatus()

        gas_price_gwei = await self.fetch_gas_price()
        if not gas_price_gwei:
            note = "Unable to fetch gas price during during ensure_staked()"
            return False, error_status(note=note, log=logger.warning)

        staker_info, read_status = await self.master.read(func_name="getStakerInfo", _staker=self.acct_addr)

        if (not read_status.ok) or (staker_info is None):
            msg = "Unable to read reporters staker status: " + read_status.error  # error won't be none # noqa: E501
            status = error_status(msg, log=logger.info)
            status.e = read_status.e
            return False, status

        logger.info(f"Stake status: {staker_info[0]}")

        # Status 1: staked
        if staker_info[0] == 1:
            return True, status

        # Status 0: not yet staked
        elif staker_info[0] == 0:
            logger.info("Address not yet staked. Depositing stake.")

            _, write_status = await self.master.write(
                func_name="depositStake",
                gas_limit=350000,
                legacy_gas_price=gas_price_gwei,
            )

            if write_status.ok:
                return True, status
            else:
                msg = (
                    "Unable to stake deposit: "
                    + write_status.error
                    + f"Make sure {self.acct_addr} has enough ETH & TRB (100)"
                )  # error won't be none # noqa: E501
                return False, error_status(msg, log=logger.info)

        # Status 3: disputed
        if staker_info[0] == 3:
            msg = "Current address disputed. Switch address to continue reporting."  # noqa: E501
            return False, error_status(msg, log=logger.info)

        # Statuses 2, 4, and 5: stake transition
        else:
            msg = "Current address is locked in dispute or for withdrawal."  # noqa: E501
            return False, error_status(msg, log=logger.info)

    async def ensure_profitable(
        self,
        datafeed: DataFeed[Any],
    ) -> ResponseStatus:
        """Estimate profitability

        Returns a bool signifying whether submitting for a given
        queryID would generate a net profit."""
        status = ResponseStatus()

        # Get current tips and time-based reward for given queryID
        rewards, read_status = await self.oracle.read("getCurrentReward", _queryId=datafeed.query.query_id)

        # Log web3 errors
        if (not read_status.ok) or (rewards is None):
            status.ok = False
            status.error = "Unable to retrieve queryID's current rewards:" + read_status.error
            logger.error(status.error)
            status.e = read_status.e
            return status

        # Fetch token prices
        price_feeds = [self.eth_usd_median_feed, self.trb_usd_median_feed]
        _ = await asyncio.gather(*[feed.source.fetch_new_datapoint() for feed in price_feeds])

        price_eth_usd = self.eth_usd_median_feed.source.latest[0]
        price_trb_usd = self.trb_usd_median_feed.source.latest[0]

        if price_eth_usd is None:
            note = "Unable to fetch ETH/USD price for profit calculation"
            return error_status(note=note, log=logger.warning)
        if price_trb_usd is None:
            note = "Unable to fetch TRB/USD price for profit calculation"
            return error_status(note=note, log=logger.warning)

        tips, tb_reward = rewards

        # Using transaction type 2 (EIP-1559)
        if self.transaction_type == 2:
            fee_info = await self.get_fee_info()
            base_fee = fee_info[0].suggestBaseFee

            # No miner tip provided by user
            if self.priority_fee is None:
                # From etherscan docs:
                # "Safe/Proposed/Fast gas price recommendations are now modeled as Priority Fees."  # noqa: E501
                # Source: https://docs.etherscan.io/api-endpoints/gas-tracker
                priority_fee = fee_info[0].SafeGasPrice
                self.priority_fee = priority_fee

            if self.max_fee is None:
                # From Alchemy docs:
                # "maxFeePerGas = baseFeePerGas + maxPriorityFeePerGas"
                # Source: https://docs.alchemy.com/alchemy/guides/eip-1559/maxpriorityfeepergas-vs-maxfeepergas  # noqa: E501
                self.max_fee = self.priority_fee + base_fee

            logger.info(
                f"""
                tips: {tips / 1e18} TRB
                time-based reward: {tb_reward / 1e18} TRB
                gas limit: {self.gas_limit}
                base fee: {base_fee}
                priority fee: {self.priority_fee}
                max fee: {self.max_fee}
                """
            )

            costs = self.gas_limit * self.max_fee

        # Using transaction type 0 (legacy)
        else:
            # Fetch legacy gas price if not provided by user
            if not self.legacy_gas_price:
                gas_price = await self.fetch_gas_price(speed=self.gas_price_speed)
                self.legacy_gas_price = gas_price

            if not self.legacy_gas_price:
                note = "Unable to fetch gas price for tx type 0"
                return error_status(note, log=logger.warning)

            logger.info(
                f"""
                tips: {tips / 1e18} TRB
                time-based reward: {tb_reward / 1e18} TRB
                gas limit: {self.gas_limit}
                legacy gas price: {self.legacy_gas_price}
                """
            )
            costs = self.gas_limit * self.legacy_gas_price

        # Calculate profit
        revenue = tb_reward + tips
        rev_usd = revenue / 1e18 * price_trb_usd
        costs_usd = costs / 1e9 * price_eth_usd
        profit_usd = rev_usd - costs_usd
        logger.info(f"Estimated profit: ${round(profit_usd, 2)}")

        percent_profit = ((profit_usd) / costs_usd) * 100
        logger.info(f"Estimated percent profit: {round(percent_profit, 2)}%")

        if (self.expected_profit != "YOLO") and (percent_profit < self.expected_profit):
            status.ok = False
            status.error = "Estimated profitability below threshold."
            logger.info(status.error)
            return status

        return status

    async def get_fee_info(self) -> Any:
        """Fetch fee into from Etherscan API.
        Source: https://etherscan.io/apis"""
        c = EtherscanGasPriceSource()
        result = await c.fetch_new_datapoint()
        return result

    async def fetch_datafeed(self) -> Optional[DataFeed[Any]]:
        if self.datafeed is None:
            suggested_qtag = await tellor_suggested_report(self.oracle)
            if suggested_qtag is None:
                logger.warning("Could not get suggested query")
                return None
            self.datafeed = CATALOG_FEEDS[suggested_qtag]  # type: ignore

        return self.datafeed

    async def get_num_reports_by_id(self, query_id: bytes) -> Tuple[int, ResponseStatus]:
        count, read_status = await self.oracle.read(func_name="getNewValueCountbyQueryId", _queryId=query_id)
        return count, read_status

    async def is_online(self) -> bool:
        return await is_online()

    def has_native_token(self) -> bool:
        return has_native_token_funds(self.acct_addr, self.endpoint._web3, min_balance=self.min_native_token_balance)

    async def report_once(
        self,
    ) -> Tuple[Optional[AttributeDict[Any, Any]], ResponseStatus]:
        """Report query value once
        This method checks to see if a user is able to submit
        values to the TellorX oracle, given their staker status
        and last submission time. Also, this method does not
        submit values if doing so won't make a profit."""
        # Check staker status
        staked, status = await self.ensure_staked()
        if not staked or not status.ok:
            logger.warning(status.error)
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

        status = await self.ensure_profitable(datafeed)
        if not status.ok:
            return None, status

        status = ResponseStatus()

        address = to_checksum_address(self.account.address)

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
        except Exception as e:
            msg = f"Error encoding response value {latest_data[0]}"
            return None, error_status(msg, e=e, log=logger.error)

        # Get nonce
        report_count, read_status = await self.get_num_reports_by_id(query_id)

        if not read_status.ok:
            status.error = "Unable to retrieve report count: " + read_status.error  # error won't be none # noqa: E501
            logger.error(status.error)
            status.e = read_status.e
            return None, status

        # Start transaction build
        submit_val_func = self.oracle.contract.get_function_by_name("submitValue")
        submit_val_tx = submit_val_func(
            _queryId=query_id,
            _value=value,
            _nonce=report_count,
            _queryData=query_data,
        )
        acc_nonce = self.endpoint._web3.eth.get_transaction_count(address)

        # Add transaction type 2 (EIP-1559) data
        if self.transaction_type == 2:
            logger.info(f"maxFeePerGas: {self.max_fee}")
            logger.info(f"maxPriorityFeePerGas: {self.priority_fee}")

            built_submit_val_tx = submit_val_tx.buildTransaction(
                {
                    "nonce": acc_nonce,
                    "gas": self.gas_limit,
                    "maxFeePerGas": Web3.toWei(self.max_fee, "gwei"),  # type: ignore
                    # TODO: Investigate more why etherscan txs using Flashbots have
                    # the same maxFeePerGas and maxPriorityFeePerGas. Example:
                    # https://etherscan.io/tx/0x0bd2c8b986be4f183c0a2667ef48ab1d8863c59510f3226ef056e46658541288 # noqa: E501
                    "maxPriorityFeePerGas": Web3.toWei(self.priority_fee, "gwei"),  # noqa: E501
                    "chainId": self.chain_id,
                }
            )
        # Add transaction type 0 (legacy) data
        else:
            # Fetch legacy gas price if not provided by user
            if not self.legacy_gas_price:
                gas_price = await self.fetch_gas_price(self.gas_price_speed)
                if not gas_price:
                    note = "Unable to fetch gas price for tx type 0"
                    return None, error_status(note, log=logger.warning)
            else:
                gas_price = self.legacy_gas_price

            built_submit_val_tx = submit_val_tx.buildTransaction(
                {
                    "nonce": acc_nonce,
                    "gas": self.gas_limit,
                    "gasPrice": Web3.toWei(gas_price, "gwei"),
                    "chainId": self.chain_id,
                }
            )

        lazy_unlock_account(self.account)
        local_account = self.account.local_account
        tx_signed = local_account.sign_transaction(built_submit_val_tx)

        # Ensure reporter lock is checked again after attempting to submit val
        self.last_submission_timestamp = 0

        try:
            logger.debug("Sending submitValue transaction")
            tx_hash = self.endpoint._web3.eth.send_raw_transaction(tx_signed.rawTransaction)
        except Exception as e:
            note = "Send transaction failed"
            return None, error_status(note, log=logger.error, e=e)

        try:
            # Confirm transaction
            tx_receipt = self.endpoint._web3.eth.wait_for_transaction_receipt(tx_hash, timeout=360)

            tx_url = f"{self.endpoint.explorer}/tx/{tx_hash.hex()}"

            if tx_receipt["status"] == 0:
                msg = f"Transaction reverted. ({tx_url})"
                return tx_receipt, error_status(msg, log=logger.error)

        except Exception as e:
            note = "Failed to confirm transaction"
            return None, error_status(note, log=logger.error, e=e)

        if status.ok and not status.error:
            logger.info(f"View reported data: \n{tx_url}")
        else:
            logger.error(status)

        return tx_receipt, status

    async def report(self, report_count: Optional[int] = None) -> None:
        """Submit values to Tellor oracles on an interval."""

        while report_count is None or report_count > 0:
            online = await self.is_online()
            if online:
                if self.has_native_token():
                    _, _ = await self.report_once()
            else:
                logger.warning("Unable to connect to the internet!")

            logger.info(f"Sleeping for {self.wait_period} seconds")
            await asyncio.sleep(self.wait_period)

            if report_count is not None:
                report_count -= 1
