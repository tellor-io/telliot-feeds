from dataclasses import dataclass

from telliot_feeds.datasource import DataSource
from telliot_feeds.dtypes.datapoint import DataPoint
from telliot_feeds.dtypes.datapoint import datetime_now_utc
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
            inpt = input().lower()

            if inpt == "y":
                val = True
            elif inpt == "n":
                val = False
            else:
                print(err_msg)
                continue

            print(f"Submitting result: {inpt}\nPress [ENTER] to confirm.")
            _ = input()

        return val

    async def fetch_new_datapoint(self) -> DataPoint[float]:
        """Update current value with time-stamped value fetched from user input.

        Returns:
            Current time-stamped value
        """
        vote = self.parse_user_val()
        datapoint = (vote, datetime_now_utc())
        self.store_datapoint(datapoint)

        return datapoint
