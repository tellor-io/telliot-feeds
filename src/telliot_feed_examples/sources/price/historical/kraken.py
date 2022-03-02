from dataclasses import dataclass
from typing import Any
from typing import Optional
from urllib.parse import urlencode

import requests
from telliot_core.dtypes.datapoint import datetime_now_utc
from telliot_core.dtypes.datapoint import OptionalDataPoint
from telliot_core.pricing.price_service import WebPriceService
from telliot_core.pricing.price_source import PriceSource

from telliot_feed_examples.utils.log import get_logger


logger = get_logger(__name__)


# Hardcoded supported assets & currencies
# Kraken uses XBT instead of BTC for its APIs:
# https://support.kraken.com/hc/en-us/articles/360001206766-Bitcoin-currency-code-XBT-vs-BTC
kraken_assets = {"ETH", "XBT"}
kraken_currencies = {"USD"}


class KrakenHistoricalPriceService(WebPriceService):
    """Kraken Historical Price Service"""

    def __init__(
        self,
        timeout: float = 0.5,
        name: str = "Kraken Historical Price Service",
        url: str = "https://api.kraken.com",
        ts: int = 0,
    ):
        self.name = name
        self.url = url
        self.ts = ts
        self.timeout = timeout

    def get_url(self, url: str = "") -> dict[str, Any]:
        """Helper function to get URL JSON response while handling exceptions

        Args:
            url: URL to fetch

        Returns:
            A dictionary with the following (optional) keys:
                json (dict or list): Result, if no error occurred
                error (str): A description of the error, if one occurred
                exception (Exception): The exception, if one occurred
        """

        request_url = self.url + url

        with requests.Session() as s:
            try:
                r = s.get(request_url, timeout=self.timeout)
                json_data = r.json()
                return {"response": json_data}

            except requests.exceptions.ConnectTimeout as e:
                return {"error": "Timeout Error", "exception": e}

            except Exception as e:
                return {"error": str(type(e)), "exception": e}

    async def get_price(
        self, asset: str, currency: str, ts: Optional[int] = None
    ) -> OptionalDataPoint[float]:
        """Implement PriceServiceInterface

        This implementation gets the historical price from
        the Kraken API using a timestamp."""
        if ts is None:
            ts = self.ts

        asset = asset.upper()
        currency = currency.upper()

        if asset not in kraken_assets:
            raise Exception(f"Asset not supported: {asset}")
        if currency not in kraken_currencies:
            raise Exception(f"Currency not supported: {currency}")

        url_params = urlencode(
            {"pair": f"{asset}{currency}", "since": ts}  # Unix timestamp
        )

        # Source: https://docs.kraken.com/rest/#operation/getRecentTrades
        request_url = f"/0/public/Trades?{url_params}"

        d = self.get_url(request_url)

        if "error" in d:
            logger.error(d)
            return None, None

        elif "response" in d:
            response = d["response"]

            try:
                price = float(response["result"][f"X{asset}Z{currency}"][0][0])
            except KeyError as e:
                msg = f"Error parsing Kraken API response: KeyError: {e}"
                logger.critical(msg)

        else:
            raise Exception("Invalid response from get_url")

        return price, datetime_now_utc()


@dataclass
class KrakenHistoricalPriceSource(PriceSource):
    ts: int = 0
    asset: str = ""
    currency: str = ""
    service: KrakenHistoricalPriceService = KrakenHistoricalPriceService(ts=ts)

    def __post_init__(self) -> None:
        self.service.ts = self.ts
