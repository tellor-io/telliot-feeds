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


# Hardcoded supported assets & currencies
# Search for supported assets here: https://api.kraken.com/0/public/Assets
KRAKEN_ASSETS = {"ETH", "MATIC", "MKR", "SUSHI", "USDC", "XBT", "WBTC"}
KRAKEN_CURRENCIES = {"USD"}


class KrakenSpotPriceService(WebPriceService):
    """Kraken Price Service"""

    def __init__(self, **kwargs: Any) -> None:
        kwargs["name"] = "Kraken Price Service"
        kwargs["url"] = "https://api.kraken.com"
        super().__init__(**kwargs)

    async def get_price(self, asset: str, currency: str) -> OptionalDataPoint[float]:
        """Implement PriceServiceInterface

        This implementation gets the price from the Kraken API."""

        asset = asset.upper()
        currency = currency.upper()

        if asset not in KRAKEN_ASSETS:
            logger.warning(f"Asset not supported: {asset}")
        if currency not in KRAKEN_CURRENCIES:
            logger.warning(f"Currency not supported: {currency}")

        url_params = urlencode({"pair": f"{asset}{currency}"})

        request_url = f"/0/public/Ticker?{url_params}"

        d = self.get_url(request_url)

        if "error" in d:
            logger.error(d)
            return None, None

        elif "response" in d:
            response = d["response"]

            try:
                price = (
                    float(response["result"][f"X{asset}Z{currency}"]["c"][0])
                    if asset in ("XBT", "ETH")
                    else float(response["result"][f"{asset}{currency}"]["c"][0])
                )
            except KeyError as e:
                msg = f"Error parsing Kraken API response: KeyError: {e}"
                logger.critical(msg)
                return None, None

        else:
            raise Exception("Invalid response from get_url")

        return price, datetime_now_utc()


@dataclass
class KrakenSpotPriceSource(PriceSource):
    asset: str = ""
    currency: str = ""
    service: KrakenSpotPriceService = field(default_factory=KrakenSpotPriceService, init=False)
