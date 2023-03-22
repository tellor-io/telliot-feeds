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


class CoinpaprikaSpotPriceService(WebPriceService):
    """Coinpaprika Price Service"""

    def __init__(self, **kwargs: Any) -> None:
        kwargs["name"] = "Coinpaprika Price Service"
        kwargs["url"] = "https://api.coinpaprika.com"
        super().__init__(**kwargs)

    async def get_price(self, asset: str, currency: str) -> OptionalDataPoint[float]:
        """Implement PriceServiceInterface

        This implementation gets the price from the Coinpaprika API."""

        asset = asset.lower()
        currency = currency.upper()

        url_params = urlencode({"quotes": f"{currency}"})

        request_url = f"/v1/tickers/{asset}?&{url_params}"

        d = self.get_url(request_url)

        if "error" in d:
            logger.error(d)
            return None, None
        elif "response" in d:
            response = d["response"]

            quote = response.get("quotes")
            if quote is None:
                logger.error("No quotes in response")
                return None, None
            quote_currency = quote.get(currency)
            if quote_currency is None:
                logger.error(f"No prices in {currency} returned from Coinpaprika API")
                return None, None

            price = quote_currency.get("price")
            if price is None:
                logger.error("Error parsing Coinpaprika API response")
                return None, None
            return price, datetime_now_utc()

        else:
            raise Exception("Invalid response from get_url")


@dataclass
class CoinpaprikaSpotPriceSource(PriceSource):
    asset: str = ""
    currency: str = ""
    service: CoinpaprikaSpotPriceService = field(default_factory=CoinpaprikaSpotPriceService, init=False)


if __name__ == "__main__":
    import asyncio

    async def main() -> None:
        source = CoinpaprikaSpotPriceSource(asset="eth-ethereum", currency="btc")
        v, _ = await source.fetch_new_datapoint()
        print(v)

    asyncio.run(main())
