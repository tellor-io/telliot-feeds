from dataclasses import dataclass
from dataclasses import field
from typing import Any
from urllib.parse import urlencode

from telliot_core.pricing.price_service import WebPriceService
from telliot_core.pricing.price_source import PriceSource
from telliot_core.types.datapoint import datetime_now_utc
from telliot_core.types.datapoint import OptionalDataPoint

from telliot_feed_examples.utils.log import get_logger


logger = get_logger(__name__)

# Hardcoded supported assets & currencies
binance_assets = {"ETH"}
binance_currencies = {"USDT", "USDC"}


class BinancePriceService(WebPriceService):
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

        if asset not in binance_assets:
            raise Exception(f"Asset not supported: {asset}")
        if currency not in binance_currencies:
            raise Exception(f"Currency not supported: {currency}")

        url_params = urlencode(
            {"symbol": f"{asset}{currency}", "interval": "1d", "limit": 1}
        )

        request_url = f"/api/v1/klines?{url_params}"

        d = self.get_url(request_url)

        if "error" in d:
            logger.error(d)
            return None, None

        elif "response" in d:
            response = d["response"]

            try:
                price = float(response[0][4])
            except KeyError as e:
                msg = f"Error parsing Binance API response: KeyError: {e}"
                logger.warning(msg)

        else:
            raise Exception("Invalid response from get_url")

        return price, datetime_now_utc()


@dataclass
class BinancePriceSource(PriceSource):
    asset: str = ""
    currency: str = ""
    service: BinancePriceService = field(
        default_factory=BinancePriceService, init=False
    )
