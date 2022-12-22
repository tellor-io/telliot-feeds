from dataclasses import dataclass

from telliot_feeds.datasource import DataSource
from telliot_feeds.dtypes.datapoint import datetime_now_utc
from telliot_feeds.dtypes.datapoint import OptionalDataPoint
from telliot_feeds.utils.input_timeout import input_timeout
from telliot_feeds.utils.input_timeout import TimeoutOccurred
from telliot_feeds.utils.log import get_logger


logger = get_logger(__name__)


@dataclass
class NumericApiManualResponse(DataSource[float]):
    """DataSource for a manually-entered numeric value."""

    def parse_user_val(self) -> float:
        """Parse user input for a numeric value."""

        print("\nType your numeric API response value and press [ENTER].\n\nFor example, type 1234 or 1234.56")

        val = None

        while val is None:
            usr_inpt = input_timeout()

            try:
                usr_inpt = float(usr_inpt)
            except ValueError:
                print("Invalid input. Enter a numerical value (float).")
                continue

            print(
                "\nNumeric API response value (with 18 decimals of precision) "
                + f"to be submitted on chain:  {usr_inpt*10**18:.0f}"
            )
            print("Press [ENTER] to confirm.")

            _ = input_timeout()

            val = usr_inpt

        return val

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

        logger.info(f"Numeric API response value {datapoint[0]} submitted at time {datapoint[1]}")

        return datapoint
