from dataclasses import dataclass
from dataclasses import field
from typing import Any

from telliot_feeds.dtypes.datapoint import datetime_now_utc
from telliot_feeds.dtypes.datapoint import OptionalDataPoint
from telliot_feeds.pricing.price_service import WebPriceService
from telliot_feeds.pricing.price_source import PriceSource
from telliot_feeds.utils.log import get_logger


logger = get_logger(__name__)


# Check supported assets here: https://api.exchange.coinbase.com/products


class CoinbaseSpotPriceService(WebPriceService):
    """Coinbase Price Service"""

    def __init__(self, **kwargs: Any) -> None:
        kwargs["name"] = "Coinbase Price Service"
        kwargs["url"] = "https://api.pro.coinbase.com"
        super().__init__(**kwargs)

    async def get_price(self, asset: str, currency: str) -> OptionalDataPoint[float]:
        """Implement PriceServiceInterface

        This implementation gets the price from the Coinbase pro API
        using the interface described at:
        https://docs.pro.coinbase.com/#products API

        Note that the timestamp returned form the coinbase API could be used
        instead of the locally generated timestamp.
        """

        request_url = "/products/{}-{}/ticker".format(asset.lower(), currency.lower())

        d = self.get_url(request_url)
        if "error" in d:
            logger.error(d)
            return None, None

        elif "response" in d:
            response = d["response"]

            if "message" in response:
                logger.error(f"API ERROR ({self.name}): {response['message']}")
                return None, None

        else:
            raise Exception("Invalid response from get_url")

        price = float(response["price"])
        return price, datetime_now_utc()


@dataclass
class CoinbaseSpotPriceSource(PriceSource):
    asset: str = ""
    currency: str = ""
    service: CoinbaseSpotPriceService = field(default_factory=CoinbaseSpotPriceService, init=False)
