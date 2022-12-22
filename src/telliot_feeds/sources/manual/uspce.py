from dataclasses import dataclass

from telliot_feeds.datasource import DataSource
from telliot_feeds.dtypes.datapoint import datetime_now_utc
from telliot_feeds.dtypes.datapoint import OptionalDataPoint
from telliot_feeds.utils.input_timeout import input_timeout
from telliot_feeds.utils.input_timeout import TimeoutOccurred
from telliot_feeds.utils.log import get_logger


logger = get_logger(__name__)


@dataclass
class USPCESource(DataSource[float]):
    """DataSource for USPCE manually-entered data."""

    def parse_user_val(test_input: str) -> float:
        """Parse USPCE value from user input."""
        # This arg is to avoid a TypeError when the default
        # input_timeout() method is overriden in test_source.py.
        # The error says this method expects no params,
        # but is passed one. TODO: fix
        _ = test_input

        print("Enter USPCE value (example: 13659.3):")

        uspce = None

        while uspce is None:
            inpt = input_timeout()

            try:
                inpt = float(inpt)
            except ValueError:
                print("Invalid input. Enter decimal value (float).")
                continue

            print(f"Submitting value: {inpt}\nPress [ENTER] to confirm.")
            _ = input_timeout()

            uspce = inpt

        return uspce

    async def fetch_new_datapoint(self) -> OptionalDataPoint[float]:
        """Update current value with time-stamped value fetched from user input.

        Returns:
            Current time-stamped value
        """
        try:
            uspce = self.parse_user_val()
        except TimeoutOccurred:
            logger.info("Timeout occurred while waiting for user input")
            return None, None

        datapoint = (uspce, datetime_now_utc())
        self.store_datapoint(datapoint)

        logger.info(f"USPCE {datapoint[0]} retrieved at time {datapoint[1]}")

        return datapoint
