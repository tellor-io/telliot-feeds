import os

from dataclasses import dataclass
from dataclasses import field
from typing import Any

from telliot_feeds.dtypes.datapoint import datetime_now_utc
from telliot_feeds.dtypes.datapoint import OptionalDataPoint
from telliot_feeds.pricing.price_service import WebPriceService
from telliot_feeds.pricing.price_source import PriceSource
from telliot_feeds.utils.log import get_logger
from dotenv import load_dotenv

load_dotenv()


logger = get_logger(__name__)

class FetchUsdMockSpotPriceService(WebPriceService):
    """FetchUsdMock Price Service"""

    def __init__(self, **kwargs: Any) -> None:
        kwargs["name"] = "FetchUsdMock Price Service"
        kwargs["url"] = ""
        super().__init__(**kwargs)

    async def get_price(self, asset: str, currency: str) -> OptionalDataPoint[float]:
        """Implement PriceServiceInterface"""

        asset = asset.lower()
        currency = currency.lower()

        if asset == "fetch" and currency == "usd" and os.getenv("FETCH_USD_MOCK_PRICE") is not None:
            return float(os.getenv("FETCH_USD_MOCK_PRICE", 1)), datetime_now_utc()

        logger.error(f"Price not found for {asset} in {currency}")
        return None, None


@dataclass
class FetchUsdMockSpotPriceSource(PriceSource):
    asset: str = ""
    currency: str = ""
    service: FetchUsdMockSpotPriceService = field(default_factory=FetchUsdMockSpotPriceService, init=False)
