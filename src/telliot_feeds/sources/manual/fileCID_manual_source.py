from typing import Optional

from telliot_feeds.datasource import DataSource
from telliot_feeds.dtypes.datapoint import datetime_now_utc
from telliot_feeds.dtypes.datapoint import OptionalDataPoint
from telliot_feeds.utils.input_timeout import input_timeout
from telliot_feeds.utils.input_timeout import TimeoutOccurred
from telliot_feeds.utils.log import get_logger


logger = get_logger(__name__)


class fileCIDManualSource(DataSource[Optional[str]]):
    async def fetch_new_datapoint(self) -> OptionalDataPoint[str]:

        print("enter CID:\n")

        try:
            usr_inpt = input_timeout()
        except TimeoutOccurred:
            logger.info("Timeout occurred while waiting for user input")
            return None, None

        print(f"\nCID to be submitted to oracle->: {usr_inpt}")
        print("Press [ENTER] to confirm.")
        try:
            _ = input_timeout()
        except TimeoutOccurred:
            logger.info("Timeout occurred while waiting for user to confirm")
            return None, None

        datapoint = (usr_inpt, datetime_now_utc())
        self.store_datapoint(datapoint)

        return datapoint
