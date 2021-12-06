from dataclasses import dataclass
from dataclasses import field
from typing import Any

import requests

from telliot_core.pricing.price_service import WebPriceService
from telliot_core.pricing.price_source import PriceSource
from telliot_core.types.datapoint import datetime_now_utc
from telliot_core.types.datapoint import OptionalDataPoint

from telliot_feed_examples.utils.log import get_logger


logger = get_logger(__name__)

# LiveCoinWatch API docs:
# https://livecoinwatch.github.io/lcw-api-docs/#coinssingle

# Hardcoded supported assets & currencies
livecoinwatch_assets = {"WAMPL"}  # used for "coin code" param
livecoinwatch_currencies = {"USD"}


class LiveCoinWatchPriceService(WebPriceService):
    """LiveCoinWatch Price Service"""

    def __init__(self, **kwargs: Any) -> None:
        kwargs["name"] = "LiveCoinWatch Price Service"
        kwargs["url"] = "https://api.livecoinwatch.com"
        super().__init__(**kwargs)

    async def get_price(self, asset: str, currency: str) -> OptionalDataPoint[float]:
        """Implement PriceServiceInterface

        This implementation gets the price from the LiveCoinWatch API."""

        asset = asset.upper()
        currency = currency.upper()

        if asset not in livecoinwatch_assets:
            raise Exception(f"Asset not supported: {asset}")
        if currency not in livecoinwatch_currencies:
            raise Exception(f"Currency not supported: {currency}")

        data = '{"currency":"' + currency + '","code":"' + asset + '","meta":false}'
        request_url = "/coins/single"
        headers = {
            'content-type': 'application/json',
            'x-api-key': '8c0752b1-1547-41ec-a558-fff37883361e',
        }

        request_url = self.url + request_url

        with requests.Session() as s:
            try:
                r = s.post(request_url, timeout=self.timeout, headers=headers, data=data)
                json_data = r.json()
                d = {"response": json_data}

            except requests.exceptions.ConnectTimeout as e:
                d = {"error": "Timeout Error", "exception": e}

            except Exception as e:
                d = {"error": str(type(e)), "exception": e}

        if "error" in d:
            logger.error(d)
            return None, None

        elif "response" in d:
            response = d["response"]

            try:
                price = float(response["rate"])
            except KeyError as e:
                msg = f"Error parsing LiveCoinWatch API response: KeyError: {e}"
                logger.critical(msg)

        else:
            raise Exception("Invalid response from get_url")

        return price, datetime_now_utc()


@dataclass
class LiveCoinWatchPriceSource(PriceSource):
    asset: str = ""
    currency: str = ""
    service: LiveCoinWatchPriceService = field(
        default_factory=LiveCoinWatchPriceService, init=False
    )
