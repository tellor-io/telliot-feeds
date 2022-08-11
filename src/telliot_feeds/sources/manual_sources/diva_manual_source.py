from dataclasses import dataclass

from telliot_feeds.datasource import DataSource
from telliot_feeds.dtypes.datapoint import OptionalDataPoint
from typing import List
from telliot_feeds.dtypes.datapoint import datetime_now_utc
from telliot_feeds.utils.log import get_logger


logger = get_logger(__name__)


def _helper(asset_collateral: str) -> float:
    asset_collateral_price = None
    print(f"Type price of the {asset_collateral} and press [ENTER]")

    while asset_collateral_price is None:
        inpt = input()
        try:
            price = float(inpt)
        except ValueError:
            print(f"Invalid {asset_collateral} price input. Enter decimal value (float).")
            continue

        asset_collateral_price = price
    return asset_collateral_price


@dataclass
class DivaManualSource(DataSource[List[float]]):
    """Datasource for Diva Protocol values"""
    def parse_user_val(self) -> List[float]:
        vals = ["reference asset", "collateral token"]

        prices = [_helper(i) for i in vals]

        with_precision = [int(i * 1e18) for i in prices]
        print(
            "\nDiva protocol reference asset and collateral token prices (with 18 decimals of precision) "
            + f"to be submitted on chain: {with_precision}"
        )
        print("Press [ENTER] to confirm.")

        _ = input()

        return prices

    async def fetch_new_datapoint(self) -> OptionalDataPoint[List[float]]:
        """Update current value with time-stamped value fetched from user input.

        Returns:
            Current time-stamped value
        """
        response = self.parse_user_val()

        datapoint = (response, datetime_now_utc())
        self.store_datapoint(datapoint)

        logger.info(f"Diva protocol prices {datapoint[0]} submitted at time {datapoint[1]}")

        return datapoint
