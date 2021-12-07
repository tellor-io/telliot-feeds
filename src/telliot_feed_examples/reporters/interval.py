""" BTCUSD Price Reporter

Example of a subclassed Reporter.
"""
import asyncio
import time
from typing import Any
from typing import Optional
from typing import Tuple

from telliot_core.contract.contract import Contract
from telliot_core.contract.gas import ethgasstation
from telliot_core.datafeed import DataFeed
from telliot_core.model.endpoints import RPCEndpoint
from telliot_core.utils.response import ResponseStatus
from web3.datastructures import AttributeDict

from telliot_feed_examples.feeds.eth_usd_feed import eth_usd_median_feed
from telliot_feed_examples.feeds.trb_usd_feed import trb_usd_median_feed
from telliot_feed_examples.utils.log import get_logger


logger = get_logger(__name__)


class IntervalReporter:
    """Reports values from given datafeeds to a TellorX Oracle
    every 10 seconds."""

    def __init__(
        self,
        endpoint: RPCEndpoint,
        private_key: str,
        master: Contract,
        oracle: Contract,
        datafeed: DataFeed[Any],
        gas_price: Optional[int] = None,
        gas_price_speed: str = "fast",
        profit_threshold: float = 0.0,
        max_gas_price: int = 0,
        gas_limit: int = 500000,
    ) -> None:

        self.endpoint = endpoint
        self.master = master
        self.oracle = oracle
        self.datafeed = datafeed
        self.user = self.endpoint.web3.eth.account.from_key(private_key).address
        self.last_submission_timestamp = 0
        self.profit_threshold = profit_threshold
        self.max_gas_price = max_gas_price
        self.gas_price_speed = gas_price_speed
        self.gas_price = gas_price
        self.gas_limit = gas_limit

        logger.info(f"Reporting with account: {self.user}")

    async def ensure_staked(self, gas_price_gwei: int) -> Tuple[bool, ResponseStatus]:
        """Make sure the current user is staked

        Returns a bool signifying whether the current address is
        staked. If the address is not initially, it attempts to stake with
        the address's funds."""
        status = ResponseStatus()

        staker_info, read_status = await self.master.read(
            "getStakerInfo", _staker=self.user
        )

        if (not read_status.ok) or (staker_info is None):
            status.ok = False
            status.error = (
                "Unable to read reporters staker status: " + read_status.error
            )  # error won't be none # noqa: E501
            status.e = read_status.e
            return False, status

        logger.info(f"Stake status: {staker_info[0]}")

        # Status 1: staked
        if staker_info[0] == 1:
            return True, status

        # Status 0: not yet staked
        elif staker_info[0] == 0:
            logger.info("Address not yet staked. Depositing stake.")

            _, write_status = await self.master.write_with_retry(
                func_name="depositStake",
                gas_price=gas_price_gwei,
                extra_gas_price=20,
                retries=5,
            )

            if write_status.ok:
                return True, status
            else:
                status.error = (
                    "Unable to stake deposit: " + write_status.error
                )  # error won't be none # noqa: E501
                logger.error(status.error)
                status.e = write_status.e
                return False, status

        # Status 3: disputed
        if staker_info[0] == 3:
            status.error = "Current address disputed. Switch address to continue reporting."  # noqa: E501
            logger.info(status.error)
            status.e = None
            return False, status

        # Statuses 2, 4, and 5: stake transition
        else:
            status.error = (
                "Current address is locked in dispute or for withdrawal."  # noqa: E501
            )
            logger.info(status.error)
            status.e = None
            return False, status

    async def check_reporter_lock(self) -> Tuple[bool, ResponseStatus]:
        """Ensure enough time has passed since last report

        Returns a bool signifying whether a given address is in a
        reporter lock or not (TellorX oracle users cannot submit
        multiple times within 12 hours)."""
        status = ResponseStatus()

        # Save last submission timestamp to reduce web3 calls
        if self.last_submission_timestamp == 0:
            last_timestamp, read_status = await self.oracle.read(
                "getReporterLastTimestamp", _reporter=self.user
            )

            # Log web3 errors
            if (not read_status.ok) or (last_timestamp is None):
                status.ok = False
                status.error = (
                    "Unable to retrieve reporter's last report timestamp:"
                    + read_status.error
                )
                logger.error(status.error)
                status.e = read_status.e
                return True, status

            self.last_submission_timestamp = last_timestamp
            logger.info(f"Last submission timestamp: {self.last_submission_timestamp}")

        if time.time() < self.last_submission_timestamp + 43200:  # 12 hours in seconds
            status.ok = False
            status.error = "Current address is in reporter lock."
            logger.info(status.error)
            return True, status

        return False, status

    async def ensure_profitable(
        self, gas_price_gwei: int
    ) -> Tuple[bool, ResponseStatus]:
        """Estimate profitability

        Returns a bool signifying whether submitting for a given
        queryID would generate a net profit."""
        status = ResponseStatus()

        # Don't check profitability if not specified by user
        if self.profit_threshold == 0.0:
            return True, status

        # Get current tips and time-based reward for given queryID
        rewards, read_status = await self.oracle.read(
            "getCurrentReward", _queryId=self.datafeed.query.query_id
        )

        # Log web3 errors
        if (not read_status.ok) or (rewards is None):
            status.ok = False
            status.error = (
                "Unable to retrieve queryID's current rewards:" + read_status.error
            )
            logger.error(status.error)
            status.e = read_status.e
            return False, status

        # Fetch token prices in USD
        price_feeds = [eth_usd_median_feed, trb_usd_median_feed]
        _ = await asyncio.gather(
            *[feed.source.fetch_new_datapoint() for feed in price_feeds]
        )
        price_eth_usd = eth_usd_median_feed.source.latest[0]
        price_trb_usd = trb_usd_median_feed.source.latest[0]

        tips, tb_reward = rewards
        logger.info(
            f"""
            current tips: {tips / 1e18} TRB
            current tb_reward: {tb_reward / 1e18} TRB
            gas_limit: {self.gas_limit}
            gas_price_gwei: {gas_price_gwei}
            """
        )

        revenue = tb_reward + tips
        rev_usd = revenue / 1e18 * price_trb_usd
        costs = self.gas_limit * gas_price_gwei
        costs_usd = costs / 1e9 * price_eth_usd
        profit_usd = rev_usd - costs_usd
        logger.info(f"Estimated profit: ${round(profit_usd, 2)}")

        percent_profit = ((profit_usd) / costs_usd) * 100
        logger.info(f"Estimated percent profit: {round(percent_profit, 2)}%")

        if not percent_profit >= self.profit_threshold:
            status.ok = False
            status.error = "Estimated profitability below threshold."
            logger.info(status.error)
            return False, status

        return True, status

    async def enforce_gas_price_limit(
        self, gas_price_gwei: int
    ) -> Tuple[bool, ResponseStatus]:
        """Ensure estimated gas price isn't above threshold.

        Returns a bool signifying whether the estimated gas price
        is under the maximum threshold chosen by the user."""
        status = ResponseStatus()

        if (self.max_gas_price != 0) and (gas_price_gwei > self.max_gas_price):
            status.ok = False
            status.error = "Estimated gas price is above maximum gas price."
            logger.error(status.error)
            return False, status

        return True, status

    async def fetch_gas_price(self) -> int:
        """Fetch gas price from ethgasstation in gwei."""
        return await ethgasstation(style=self.gas_price_speed)  # type: ignore

    async def report_once(
        self,
    ) -> Tuple[Optional[AttributeDict[Any, Any]], ResponseStatus]:
        """Report query value once

        This method checks to see if a user is able to submit
        values to the TellorX oracle, given their staker status
        and last submission time. Also, this method does not
        submit values if doing so won't make a profit."""

        reporter_locked, status = await self.check_reporter_lock()
        if reporter_locked:
            return None, status

        # Custom gas price overrides other gas price settings
        gas_price_gwei = self.gas_price
        if gas_price_gwei is None:
            gas_price_gwei = await self.fetch_gas_price()

            gas_price_below_limit, status = await self.enforce_gas_price_limit(
                gas_price_gwei
            )
            if not gas_price_below_limit:
                return None, status

        staked, status = await self.ensure_staked(gas_price_gwei)
        if not staked:
            return None, status

        profitable, status = await self.ensure_profitable(gas_price_gwei)
        if not profitable:
            return None, status

        status = ResponseStatus()

        # Update value
        await self.datafeed.source.fetch_new_datapoint()
        latest_data = self.datafeed.source.latest

        if latest_data[0] is None:
            status.ok = False
            status.error = "Unable to retrieve updated datafeed value."
            logger.error(status.error)
            return None, status

        query = self.datafeed.query

        value = query.value_type.encode(latest_data[0])
        query_id = query.query_id
        query_data = query.query_data
        extra_gas_price = 20

        timestamp_count, read_status = await self.oracle.read(
            func_name="getTimestampCountById", _queryId=query_id
        )

        # Log web3 errors
        if not read_status.ok:
            status.error = (
                "Unable to retrieve timestampCount: " + read_status.error
            )  # error won't be none # noqa: E501
            logger.error(status.error)
            status.e = read_status.e
            return None, status

        # Submit value
        tx_receipt, status = await self.oracle.write_with_retry(
            func_name="submitValue",
            gas_price=gas_price_gwei,
            extra_gas_price=extra_gas_price,
            retries=5,
            _queryId=query_id,
            _value=value,
            _nonce=timestamp_count,
            _queryData=query_data,
        )

        if status.ok and not status.error:
            # Reset previous submission timestamp
            self.last_submission_timestamp = 0
            tx_hash = tx_receipt["transactionHash"].hex()
            # Point to relevant explorer
            logger.info(f"View reported data: \n{self.endpoint.explorer}/tx/{tx_hash}")
        else:
            logger.error(status)

        return tx_receipt, status

    async def report(self) -> None:
        """Submit latest values to the TellorX oracle every 12 hours."""

        while True:
            _, _ = await self.report_once()
            await asyncio.sleep(10)
