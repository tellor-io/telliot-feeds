from dataclasses import dataclass
from dataclasses import field
from typing import Any

from telliot_core.pricing.price_service import WebPriceService
from telliot_core.pricing.price_source import PriceSource
from telliot_core.types.datapoint import datetime_now_utc
from telliot_core.types.datapoint import OptionalDataPoint

from telliot_feed_examples.utils.log import get_logger


logger = get_logger(__name__)


# Hardcoded supported assets & currencies
bitfinex_assets = {"ETH"}
bitfinex_currencies = {"JPY"}


class BitfinexPriceService(WebPriceService):
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

        request_url = f"/v2/ticker/t{asset}{currency}"

        d = self.get_url(request_url)

        if "error" in d:
            logger.error(d)
            return None, None

        elif "response" in d:
            response = d["response"]

            try:
                price = float(response[6])
            except KeyError as e:
                msg = f"Error parsing Coingecko API response: KeyError: {e}"
                logger.critical(msg)

        else:
            raise Exception("Invalid response from get_url")

        return price, datetime_now_utc()


@dataclass
class BitfinexPriceSource(PriceSource):
    asset: str = ""
    currency: str = ""
    service: BitfinexPriceService = field(
        default_factory=BitfinexPriceService, init=False
    )
