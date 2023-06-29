import asyncio
from dataclasses import dataclass
from typing import Any
from typing import Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

from telliot_feeds.datasource import DataSource
from telliot_feeds.dtypes.datapoint import datetime_now_utc
from telliot_feeds.dtypes.datapoint import OptionalDataPoint
from telliot_feeds.utils.log import get_logger

logger = get_logger(__name__)

retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"],
)
adapter = HTTPAdapter(max_retries=retry_strategy)

supported_assets = ["rice", "wheat", "soy", "corn"]


@dataclass
class LandXSource(DataSource[Any]):
    """Source that fetches commodity data from the LandX maintained API,
    https://api-testnet.landx.fi/api/public/commodities.
    only assets supported are ["rice", "wheat", "soybean", "corn"]
    """

    asset: Optional[str] = None

    def fetch_commodities_prices(self) -> Optional[Any]:
        with requests.Session() as s:
            s.mount("https://", adapter)
            try:
                rsp = s.get("https://api-testnet.landx.fi/api/public/commodities")
                return rsp.json()
            except requests.exceptions.ConnectTimeout:
                logger.error("Connection timeout getting commodities prices")
                return None
            except requests.exceptions.RequestException as e:
                logger.error(f"LandX api error: {e}")
                return None

    async def fetch_new_datapoint(self) -> OptionalDataPoint[Any]:
        """Fetch commodities prices for rice, wheat, soybean, and corn."""
        if self.asset is None:
            raise ValueError("LandXSource asset not set, required")
        if self.asset.lower() not in supported_assets:
            logger.error(f"LandXSource asset {self.asset} not supported")
            return None, None

        prices = self.fetch_commodities_prices()

        if not isinstance(prices, dict):
            logger.error("Invalid response from LandX API for commodities prices")
            return None, None
        price = prices.get(self.asset.upper())
        if price is None:
            logger.error(f"Asset {self.asset} not found in LandX API response")
            return None, None
        datapoint = (price, datetime_now_utc())
        self.store_datapoint(datapoint)
        return datapoint


if __name__ == "__main__":
    for asset in supported_assets:
        print(asyncio.run(LandXSource(asset=asset).fetch_new_datapoint()))
