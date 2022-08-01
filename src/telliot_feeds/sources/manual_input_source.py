from ast import literal_eval
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

        print("Enter vote:")

        val = None
        msg = "Invalid input. Enter True/False or 0/1 value (bool)."
        while val is None:
            inpt = input()

            if inpt == "1":
                return True
            elif inpt == "0":
                return False
            else:
                try:
                    inpt = literal_eval(inpt.capitalize())
                    assert type(inpt) is bool  # type: ignore
                except AssertionError:
                    print(msg)
                    continue
                except ValueError:
                    print(msg)
                    continue

            print(f"Submitting value: {inpt}\nPress [ENTER] to confirm.")
            _ = input()

            val = inpt

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
