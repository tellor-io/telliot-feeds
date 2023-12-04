import asyncio
from dataclasses import dataclass
from typing import Any
from typing import Optional

from eth_abi.abi import decode_abi

from telliot_feeds.reporters.tellor_360 import Tellor360Reporter
from telliot_feeds.utils.log import get_logger
from telliot_feeds.utils.reporter_utils import current_time

from telliot_feeds.sources.price_aggregator import PriceAggregator

logger = get_logger(__name__)


@dataclass
class GetDataBefore:
    retrieved: bool
    value: bytes
    timestampRetrieved: int


@dataclass
class ConditionalReporter(Tellor360Reporter):
    """For Reporting Spot Prices when spot price median feed 
    returns a value that is too different from GetDataBefore, 
    and/or when the GetDataBefore returns a timestamp that is too old."""

    def __init__(
        self,
        tellor_is_stale_timeout: int,
        tellor_max_price_change: float,
        query_tag: str,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.tellor_is_stale_timeout = tellor_is_stale_timeout
        self.tellor_max_price_change = tellor_max_price_change
        self.query_tag = query_tag


    async def get_tellor_latest_data(self) -> Optional[GetDataBefore]:
        """Get latest data from tellor oracle (getDataBefore with current time)

        Returns:
        - Optional[GetDataBefore]: latest data from tellor oracle
        """
        if self.datafeed is None:
            logger.debug(f"no datafeed set: {self.datafeed}")
            return None
        data, status = await self.oracle.read("getDataBefore", self.datafeed.query.query_id, current_time())
        if not status.ok:
            logger.warning(f"error getting tellor data: {status.e}")
            return None
        return GetDataBefore(*data)

    async def get_spot_price_feed(self) -> 

    def tellor_price_change_above_max(
        self, tellor_latest_data: GetDataBefore,
    ) -> bool:
        """Check difference in value between latest tellor report and current aggregator price
        params:
        - chainlink_latest_round_data: latest round data from chainlink feed
        - chainlink_previous_round_data: previous round data from chainlink feed

        Returns:
        - bool: True if price change is above max price deviation, False otherwise
        """
        current_price = tellor_latest_data.answer
        previous_price = tellor_latest_data.answer

        min_price = min(current_price, previous_price)
        max_price = max(current_price, previous_price)

        percent_change = (max_price - min_price) / max_price
        if percent_change > self.tellor_max_price_change:
            logger.info("tellor price change above max")
            return True
        else:
            return False

    def tellor_is_stale(self, tellor_latest_data: GetDataBefore) -> bool:
        """Check if tellor is frozen based on timestamp of last report

        params:
        - chainlink_latest_round_data: latest round data from chainlink feed

        Returns:
        - bool: True if chainlink is data is stale, False otherwise
        """
        current_timestamp = current_time()
        latest_timestamp = tellor_latest_data.timestampRetrieved
        if current_timestamp - latest_timestamp > self.no_tellor_report_timeout:
            logger.info(f"tellor is almost stale. latest timestamp: {latest_timestamp}")
            return True
        else:
            return False


    async def conditions_met(self) -> bool:
        """Trigger methods to check conditions if reporting spot is necessary

        Returns:
        - bool: True if conditions are met, False otherwise
        """
        logger.info("checking conditions and reporting if necessary")
        if self.datafeed is None:
            logger.debug(f"no datafeed was setß: {self.datafeed}")
            return False
        tellor_data = await self.get_tellor_latest_data()
        time = current_time()
        time_passed_since_tellor_report = time - tellor_data.timestampRetrieved if tellor_data else time
        if tellor_data is None:
            logger.debug("tellor data returned None")
        elif not tellor_data.retrieved:
            logger.debug(f"No oracle submissions in tellor for query: {self.datafeed.query.descriptor}")
        elif time_passed_since_tellor_report > self.no_tellor_report_timeout:
            logger.debug(f"tellor data is stale, time elapsed since last report: {time_passed_since_tellor_report}")
        else:
            logger.info(f"tellor {self.datafeed.query.descriptor} data is recent enough")
            return False

        latest_tellor_data = self.get_tellor_latest_data()

        if latest_tellor_data is None:
            return True
        if self.tellor_is_stale(latest_tellor_data):
            return True

        check_spot_price_feed = self.get_chainlink_previous_round_data(chainlink_latest_round_data.roundId)

        if chainlink_previous_round_data is None:
            return True

        if self.chainlink_price_change_above_max(chainlink_latest_round_data, chainlink_previous_round_data):
            return True
        logger.info(f"chainLink {self.datafeed.query.descriptor} data is recent enough")
        return False



    async def report(self, report_count: Optional[int] = None) -> None:
        """Submit values to Tellor oracles on an interval."""

        while report_count is None or report_count > 0:
            online = await self.is_online()
            if online:
                if self.has_native_token():
                    if await self.conditions_met():
                        _, _ = await self.report_once()
                    else:
                        logger.info("feeds are recent enough, no need to report")

            else:
                logger.warning("Unable to connect to the internet!")

            logger.info(f"Sleeping for {self.wait_period} seconds")
            await asyncio.sleep(self.wait_period)

            if report_count is not None:
                report_count -= 1
