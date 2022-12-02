from dataclasses import dataclass
from dataclasses import field
from typing import Any
from urllib.parse import urlencode

from telliot_feeds.dtypes.datapoint import datetime_now_utc
from telliot_feeds.dtypes.datapoint import OptionalDataPoint
from telliot_feeds.pricing.price_service import WebPriceService
from telliot_feeds.pricing.price_source import PriceSource
from telliot_feeds.utils.log import get_logger


logger = get_logger(__name__)


class BinanceSpotPriceService(WebPriceService):
    """Binance Price Service"""

    def __init__(self, **kwargs: Any) -> None:
        kwargs["name"] = "Binance Price Service"
        kwargs["url"] = "https://api.binance.com"
        super().__init__(**kwargs)

    async def get_price(self, asset: str, currency: str) -> OptionalDataPoint[float]:
        """Implement PriceServiceInterface

        This implementation gets the price from the Binance API."""

        asset = asset.upper()
        currency = currency.upper()

        url_params = urlencode({"symbol": f"{asset}{currency}", "interval": "1d", "limit": 1})

        request_url = f"/api/v1/klines?{url_params}"

        d = self.get_url(request_url)

        if "error" in d:
            logger.error(d)
            return None, None

        elif "response" in d:
            response = d["response"]

            if isinstance(response, dict) and "msg" in response:
                logger.warning(response["msg"])
                return None, None

            if isinstance(response, list) and len(response) == 0:
                logger.info("No data returned from Binance")
                return None, None

            try:
                price = float(response[0][4])
                return price, datetime_now_utc()
            except Exception as e:
                msg = f"Error parsing Binance API response. Error: {e}"
                logger.warning(msg)
                return None, None

        else:
            raise Exception("Invalid response from get_url")


@dataclass
class BinanceSpotPriceSource(PriceSource):
    asset: str = ""
    currency: str = ""
    service: BinanceSpotPriceService = field(default_factory=BinanceSpotPriceService, init=False)
