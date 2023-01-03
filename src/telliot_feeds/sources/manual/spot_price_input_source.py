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
class SpotPriceManualSource(DataSource[float]):
    """DataSource for a spot-price manually-entered data."""

    def parse_user_val(self) -> float:
        """Parse user input for a spot price value."""

        print("\nType your spot price and press [ENTER].\n\nFor example, if price is $1234.0, type 1234 or 1234.0")

        spot = None

        while spot is None:
            usr_inpt = input_timeout()

            try:
                usr_inpt = float(usr_inpt)
            except ValueError:
                print("Invalid input. Enter decimal value (float).")
                continue

            print(f"\nSpot price (with 18 decimals of precision) to be submitted on chain: {usr_inpt*10**18:.0f}")
            print("Press [ENTER] to confirm.")

            _ = input_timeout()

            spot = usr_inpt

        return spot

    async def fetch_new_datapoint(self) -> OptionalDataPoint[float]:
        """Update current value with time-stamped value fetched from user input.

        Returns:
            Current time-stamped value
        """
        try:
            price = self.parse_user_val()
        except TimeoutOccurred:
            logger.info("Timeout occurred while waiting for user input")
            return None, None

        datapoint = (price, datetime_now_utc())
        self.store_datapoint(datapoint)

        logger.info(f"Spot price {datapoint[0]} retrieved at time {datapoint[1]}")

        return datapoint


if __name__ == "__main__":
    spot = SpotPriceManualSource()
    v, t = asyncio.run(spot.fetch_new_datapoint())
    print("datapoint:", v, t)
