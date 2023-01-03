from dataclasses import dataclass

from telliot_feeds.datasource import DataSource
from telliot_feeds.dtypes.datapoint import datetime_now_utc
from telliot_feeds.dtypes.datapoint import OptionalDataPoint
from telliot_feeds.utils.input_timeout import input_timeout
from telliot_feeds.utils.input_timeout import TimeoutOccurred
from telliot_feeds.utils.log import get_logger


logger = get_logger(__name__)


@dataclass
class DailyVolatilityManualSource(DataSource[float]):
    """DataSource for a manually-entered Volatility index."""

    def parse_user_val(self) -> float:
        """Parse user input"""

        print("\nType your Volatility index response and press [ENTER].\n\nFor example, type 3.0 or 3.56")

        num = None

        while num is None:
            usr_inpt = input_timeout()

            try:
                inpt = float(usr_inpt)
            except ValueError:
                print("Invalid input. Enter a decimal value (float).")
                continue
            if inpt < 0:
                print("Invalid input. Number must greater than 0.")
                continue

            print(f"\nVolatility index (with 18 decimals of precision) to be submitted on chain:  {inpt*10**18:.0f}")
            print("Press [ENTER] to confirm.")

            _ = input_timeout()

            num = inpt

        return num

    async def fetch_new_datapoint(self) -> OptionalDataPoint[float]:
        """Update current value with time-stamped value fetched from user input.

        Returns:
            Current time-stamped value
        """
        try:
            response = self.parse_user_val()
        except TimeoutOccurred:
            logger.info("Timeout occurred while waiting for user input")
            return None, None

        datapoint = (response, datetime_now_utc())
        self.store_datapoint(datapoint)

        logger.info(f"Volatility index {datapoint[0]} submitted at time {datapoint[1]}")

        return datapoint
