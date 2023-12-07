import asyncio
from dataclasses import dataclass
from typing import Any
from typing import Optional
from typing import TypeVar

from telliot_feeds.feeds import DataFeed
from telliot_feeds.datasource import OptionalDataPoint
from telliot_feeds.reporters.tellor_360 import Tellor360Reporter
from telliot_feeds.utils.log import get_logger
from telliot_feeds.utils.reporter_utils import current_time
from telliot_feeds.feeds.eth_usd_feed import eth_usd_median_feed

logger = get_logger(__name__)
T = TypeVar("T")

@dataclass
class GetDataBefore:
    retrieved: bool
    value: bytes
    timestampRetrieved: int


@dataclass
class ConditionalReporter(Tellor360Reporter):
    """Backup Reporter that inherits from Tellor360Reporter and
    implements conditions when intended as backup to chainlink"""

    def __init__(
        self,
        stale_timeout: int,
        max_price_change: float,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.stale_timeout = stale_timeout
        self.max_price_change = max_price_change

    def get_tellor_latest_data(self) -> Optional[GetDataBefore]:
        """Get latest data from tellor oracle (getDataBefore with current time)
        Returns:
        - Optional[GetDataBefore]: latest data from tellor oracle
        """
        if self.datafeed is None:
            logger.debug(f"no datafeed set: {self.datafeed}")
            return None
        data, status = self.oracle.read("getDataBefore", self.datafeed.query.query_id, current_time())
        if not status.ok:
            logger.warning(f"error getting tellor data: {status.e}")
            return None
        return GetDataBefore(*data)
    
    def get_telliot_feed_data(self) -> OptionalDataPoint[T]:
        """Fetch spot price data from API sources and calculate a value
        Returns:
        - Optional[GetDataBefore]: latest data from tellor oracle
        """
        v, _ = eth_usd_median_feed.source.fetch_new_datapoint()
        logger.info(f"telliot feeds value: {v}")
        return v

    def tellor_price_change_above_max(
        self, tellor_latest_data: GetDataBefore, telliot_feed_data: OptionalDataPoint
    ) -> bool:
        """Check if spot price change since last report is above max price deviation
        params:
        - tellor_latest_data: latest data from tellor oracle
        - telliot_feed_data: latest data from API sources

        Returns:
        - bool: True if price change is above max price deviation, False otherwise
        """
        oracle_price = tellor_latest_data.answer
        feed_price = telliot_feed_data.answer

        min_price = min(oracle_price, feed_price)
        max_price = max(oracle_price, feed_price)

        percent_change = (max_price - min_price) / max_price
        if percent_change > self.max_price_change:
            logger.info("feed price change above max")
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
            logger.debug(f"no datafeed was setß: {self.datafeed}. Please provide a spot-price query type (see --help)")
            return False
        tellor_latest_data = await self.get_tellor_latest_data()
        telliot_feed_data = self.get_telliot_feed_data()
        time = current_time()
        time_passed_since_tellor_report = time - tellor_latest_data.timestampRetrieved if tellor_latest_data else time
        if tellor_latest_data is None:
            logger.debug("tellor data returned None")
            return True
        elif not tellor_latest_data.retrieved:
            logger.debug(f"No oracle submissions in tellor for query: {self.datafeed.query.descriptor}")
            return True
        elif time_passed_since_tellor_report > self.stale_timeout:
            logger.debug(f"tellor data is stale, time elapsed since last report: {time_passed_since_tellor_report}")
            return True
        elif self.tellor_price_change_above_max(tellor_latest_data, telliot_feed_data):
            return True 
        else:
            logger.info(f"tellor {self.datafeed.query.descriptor} data is recent enough")
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
