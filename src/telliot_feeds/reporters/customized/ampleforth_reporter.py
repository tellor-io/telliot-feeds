import asyncio
from dataclasses import dataclass
from datetime import datetime
from datetime import timedelta
from typing import Any
from typing import Optional
from typing import TypeVar

from pytz import timezone

from telliot_feeds.feeds import DataFeed
from telliot_feeds.reporters.tellor_360 import Tellor360Reporter
from telliot_feeds.utils.log import get_logger
from telliot_feeds.utils.reporter_utils import current_time

logger = get_logger(__name__)
T = TypeVar("T")


@dataclass
class GetDataBefore:
    retrieved: bool
    value: bytes
    timestampRetrieved: int


@dataclass
class AmpleforthReporter(Tellor360Reporter):
    """Backup Reporter that inherits from Tellor360Reporter and
    implements conditions when intended as backup to chainlink"""

    def __init__(
        self,
        backup_check_time: int = 1080,
        datafeed: Optional[DataFeed[Any]] = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.backup_check_time = backup_check_time
        self.datafeed = datafeed
        self.qtag_selected = True

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

    def check_ampleforth_custom(self, tellor_latest_data: GetDataBefore) -> bool:
        """check if ampleforth-custom was reported soon after 00:00:00 UTC
        params:
        - tellor_latest_data: latest data from tellor oracle
        Returns:
        - bool: True if ampleforth-custom was not reported
                between UTC 00:08:00 and 00:18:00
        False if there was a report in that window.
        """
        now_utc = datetime.now(timezone("UTC"))
        midnight_utc = now_utc.replace(hour=0, minute=0, second=0, microsecond=0)
        open_window = midnight_utc + timedelta(seconds=10)
        close_window = midnight_utc + timedelta(seconds=self.backup_check_time)
        ampl_report = tellor_latest_data.timestampRetrieved
        if now_utc >= close_window:
            logger.info(f"checking if ampleforth-custom was reported by {close_window}")
            if ampl_report < (open_window).timestamp():
                logger.info("no ampleforth report found!")
                return True
            else:
                logger.info("ampleforth-custom was reported.")
                return False
        else:
            return False

    async def conditions_met(self) -> bool:
        """Trigger methods to check conditions if reporting spot is necessary

        Returns:
        - bool: True if conditions are met, False otherwise
        """
        logger.info("Checking conditions and reporting if necessary! \U0001F44D")
        # Get latest report from Tellor
        tellor_latest_data = await self.get_tellor_latest_data()
        if tellor_latest_data is None:
            logger.debug("tellor data returned None")
            return True
        elif not tellor_latest_data.retrieved:
            logger.debug("No oracle submission found for ampleforth-custom...")
            return True
        elif self.check_ampleforth_custom(tellor_latest_data):
            logger.debug("ampleforth-custom report was not found in the window...")
            return True
        else:
            logger.debug("\U0001F44C no need to report ampleforth-custom")
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
