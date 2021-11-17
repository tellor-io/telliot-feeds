from dataclasses import dataclass
from dataclasses import field
from typing import Any

from telliot_core.pricing.price_service import WebPriceService
from telliot_core.pricing.price_source import PriceSource
from telliot_core.types.datapoint import datetime_now_utc
from telliot_core.types.datapoint import OptionalDataPoint


class CoinbasePriceService(WebPriceService):
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
            print(d)  # TODO: Log
            return None, None

        elif "response" in d:
            response = d["response"]

            if "message" in response:
                print("API ERROR ({}): {}".format(self.name, response["message"]))
                return None, None

        else:
            raise Exception("Invalid response from get_url")

        price = float(response["price"])
        return price, datetime_now_utc()


@dataclass
class CoinbasePriceSource(PriceSource):
    asset: str = ""
    currency: str = ""
    service: CoinbasePriceService = field(
        default_factory=CoinbasePriceService, init=False
    )
