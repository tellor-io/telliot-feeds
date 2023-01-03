import asyncio
from dataclasses import dataclass

from telliot_feeds.datasource import DataSource
from telliot_feeds.dtypes.datapoint import datetime_now_utc
from telliot_feeds.dtypes.datapoint import OptionalDataPoint
from telliot_feeds.utils.input_timeout import input_timeout
from telliot_feeds.utils.input_timeout import TimeoutOccurred
from telliot_feeds.utils.log import get_logger


logger = get_logger(__name__)


@dataclass
class ManualSnapshotInputSource(DataSource[float]):
    """DataSource for Snapshot Vote manually-entered data."""

    def parse_user_val(self) -> float:
        msg = "Did vote pass or fail? Enter (y/n): "
        print(msg)

        err_msg = "Invalid input. " + msg
        val = None
        while val is None:
            inpt = input_timeout().lower()

            if inpt == "y":
                val = True
            elif inpt == "n":
                val = False
            else:
                print(err_msg)
                continue

            print(f"Submitting result: {inpt}\nPress [ENTER] to confirm.")
            _ = input_timeout()

        return val

    async def fetch_new_datapoint(self) -> OptionalDataPoint[float]:
        """Update current value with time-stamped value fetched from user input.

        Returns:
            Current time-stamped value
        """
        try:
            vote = self.parse_user_val()
        except TimeoutOccurred:
            logger.info("Timeout occurred while waiting for user input")
            return None, None
        datapoint = (vote, datetime_now_utc())
        self.store_datapoint(datapoint)

        return datapoint


if __name__ == "__main__":
    s = ManualSnapshotInputSource()
    v, t = asyncio.run(s.fetch_new_datapoint())
    print("datapoint:", v, t)
