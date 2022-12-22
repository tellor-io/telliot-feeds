from dataclasses import dataclass
from typing import Optional

from telliot_feeds.datasource import DataSource
from telliot_feeds.dtypes.datapoint import datetime_now_utc
from telliot_feeds.dtypes.datapoint import OptionalDataPoint
from telliot_feeds.utils.input_timeout import input_timeout
from telliot_feeds.utils.input_timeout import TimeoutOccurred
from telliot_feeds.utils.log import get_logger


logger = get_logger(__name__)


def get_price_from_user(param: str) -> float:
    """Parse price from user input."""
    param_price = None
    print(f"Type price of {param} and press [ENTER]")

    while param_price is None:
        inpt = input_timeout()
        try:
            price = float(inpt)
        except ValueError:
            print(f"Invalid {param} price input. Enter decimal value (float).")
            continue
        if price < 0:
            print(f"Invalid {param} price input. Number must greater than 0.")
            continue

        param_price = price
    return param_price


@dataclass
class DivaManualSource(DataSource[list[float]]):
    """Datasource for Diva Protocol values"""

    reference_asset: Optional[str] = None
    collateral_token: Optional[str] = None

    def parse_user_val(self) -> list[float]:
        """Parse user input and return list of prices."""
        params = ["reference asset", "collateral token"]
        params[0] = self.reference_asset if self.reference_asset is not None else params[0]
        params[1] = self.collateral_token if self.collateral_token is not None else params[1]

        prices = [get_price_from_user(i) for i in params]

        with_precision = [int(i * 1e18) for i in prices]
        print(
            "\nDiva protocol reference asset and collateral token prices (with 18 decimals of precision) "
            + f"to be submitted on chain: {with_precision}"
        )
        print("Press [ENTER] to confirm.")

        _ = input_timeout()

        return prices

    async def fetch_new_datapoint(self) -> OptionalDataPoint[list[float]]:
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

        logger.info(f"Diva protocol prices {datapoint[0]} submitted at time {datapoint[1]}")

        return datapoint
