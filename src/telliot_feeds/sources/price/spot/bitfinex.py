from dataclasses import dataclass
from dataclasses import field
from typing import Any

from telliot_feeds.dtypes.datapoint import datetime_now_utc
from telliot_feeds.dtypes.datapoint import OptionalDataPoint
from telliot_feeds.pricing.price_service import WebPriceService
from telliot_feeds.pricing.price_source import PriceSource
from telliot_feeds.utils.log import get_logger


logger = get_logger(__name__)


# Hardcoded supported assets & currencies
bitfinex_assets = {"ETH", "TLOS"}
bitfinex_currencies = {"JPY", "USD"}


class BitfinexSpotPriceService(WebPriceService):
    """Bitfinex Price Service"""

    def __init__(self, **kwargs: Any) -> None:
        kwargs["name"] = "Bitfinex Price Service"
        kwargs["url"] = "https://api-pub.bitfinex.com"
        super().__init__(**kwargs)

    async def get_price(self, asset: str, currency: str) -> OptionalDataPoint[float]:
        """Implement PriceServiceInterface

        This implementation gets the price from the Bitfinex API."""

        asset = asset.upper()
        currency = currency.upper()

        if asset not in bitfinex_assets:
            raise Exception(f"Asset not supported: {asset}")
        if currency not in bitfinex_currencies:
            raise Exception(f"Currency not supported: {currency}")

        request_url = f"/v2/ticker/t{asset}:{currency}"

        d = self.get_url(request_url)

        if "error" in d:
            logger.error(d)
            return None, None

        elif "response" in d:
            response = d["response"]

            try:
                price = float(response[6])
                return price, datetime_now_utc()
            except Exception as e:
                msg = f"Error parsing Bitfinex API response: Exception: {e}"
                logger.critical(msg)
                return None, None

        else:
            logger.critical("Invalid response from get_url")
            return None, None


@dataclass
class BitfinexSpotPriceSource(PriceSource):
    asset: str = ""
    currency: str = ""
    service: BitfinexSpotPriceService = field(default_factory=BitfinexSpotPriceService, init=False)
