from dataclasses import dataclass
from dataclasses import field
from typing import Any

from telliot_feeds.dtypes.datapoint import datetime_now_utc
from telliot_feeds.dtypes.datapoint import OptionalDataPoint
from telliot_feeds.pricing.price_service import WebPriceService
from telliot_feeds.pricing.price_source import PriceSource
from telliot_feeds.utils.log import get_logger


logger = get_logger(__name__)


class CryptodotcomSpotPriceService(WebPriceService):
    """Crypto.com Price Service"""

    def __init__(self, **kwargs: Any) -> None:
        kwargs["name"] = "Crypto.com Price Service"
        kwargs["url"] = "https://api.crypto.com"
        super().__init__(**kwargs)

    async def get_price(self, asset: str, currency: str) -> OptionalDataPoint[float]:
        """Implement PriceServiceInterface

        This implementation gets the price from the Cryto.com api.
        e.g. request https://api.crypto.com/v2/public/get-ticker?instrument_name=TRB_USDT
        https://github.com/IgorJakovljevic/crypto-exchange?tab=readme-ov-file#endpoint
        """

        market_symbol = f"{format(asset.upper())}_{format(currency.upper())}"
        request_url = f"/v2/public/get-ticker?instrument_name={market_symbol}"

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

        price = float(response["result"]["data"][0]["a"])
        return price, datetime_now_utc()


@dataclass
class CryptodotcomSpotPriceSource(PriceSource):
    asset: str = ""
    currency: str = ""
    service: CryptodotcomSpotPriceService = field(default_factory=CryptodotcomSpotPriceService, init=False)


if __name__ == "__main__":
    import asyncio

    async def main() -> None:
        source = CryptodotcomSpotPriceSource(asset="eth", currency="usd")
        v, _ = await source.fetch_new_datapoint()
        print(v)

    asyncio.run(main())
