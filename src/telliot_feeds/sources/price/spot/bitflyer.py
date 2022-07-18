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
bitflyer_assets = {"ETH"}
bitflyer_currencies = {"JPY"}


class BitflyerSpotPriceService(WebPriceService):
    """Bitflyer Price Service"""

    def __init__(self, **kwargs: Any) -> None:
        kwargs["name"] = "Bitflyer Price Service"
        kwargs["url"] = "https://api.bitflyer.com"
        super().__init__(**kwargs)

    async def get_price(self, asset: str, currency: str) -> OptionalDataPoint[float]:
        """Implement PriceServiceInterface

        This implementation gets the price from the Bitflyer API."""

        asset = asset.upper()
        currency = currency.upper()

        if asset not in bitflyer_assets:
            raise Exception(f"Asset not supported: {asset}")
        if currency not in bitflyer_currencies:
            raise Exception(f"Currency not supported: {currency}")

        asset_currency = asset + "_" + currency

        url_params = urlencode({"product_code": asset_currency})
        request_url = f"/v1/getticker?{url_params}"

        d = self.get_url(request_url)

        if "error" in d:
            logger.error(d)
            return None, None

        elif "response" in d:
            response = d["response"]

            try:
                price = float(response["ltp"])
            except KeyError as e:
                msg = f"Error parsing Coingecko API response: KeyError: {e}"
                logger.critical(msg)

        else:
            raise Exception("Invalid response from get_url")

        return price, datetime_now_utc()


@dataclass
class BitflyerSpotPriceSource(PriceSource):
    asset: str = ""
    currency: str = ""
    service: BitflyerSpotPriceService = field(default_factory=BitflyerSpotPriceService, init=False)
