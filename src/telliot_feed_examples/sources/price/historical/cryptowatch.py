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


# Hardcoded supported asset/currency pairs
CRYPTOWATCH_PAIRS = {"ethusd", "btcusd"}


class CryptowatchHistoricalPriceService(WebPriceService):
    """Cryptowatch Historical Price Service"""

    def __init__(
        self,
        timeout: float = 0.5,
        name: str = "Cryptowatch Historical Price Service",
        url: str = "https://api.cryptowat.ch/",
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
        the Cryptowatch API using a timestamp. Historical prices are
        fetched from Cryptowatch's recorded Coinbase-pro data.

        Documentation for Cryptowatch API:
        https://docs.cryptowat.ch/rest-api/markets/ohlc
        """
        if ts is None:
            ts = self.ts

        asset = asset.lower()
        currency = currency.lower()
        pair = asset + currency

        if pair not in CRYPTOWATCH_PAIRS:
            raise Exception(f"Currency pair not supported: {pair}")

        periods = 1800  # 30min
        url_params = urlencode(
            {"after": int(ts - 1e4), "before": ts, "periods": periods}
        )

        request_url = f"markets/coinbase-pro/{pair}/ohlc?{url_params}"

        d = self.get_url(request_url)
        price = None

        if "error" in d:
            logger.error(d)
            return None, None

        elif "response" in d:
            response = d["response"]

            try:
                price = float(response["result"][str(periods)][-1][4])
            except KeyError as e:
                msg = f"Error parsing Cryptowatch API response: KeyError: {e}"
                logger.critical(msg)

        else:
            raise Exception("Invalid response from get_url")

        return price, datetime_now_utc()


@dataclass
class CryptowatchHistoricalPriceSource(PriceSource):
    ts: int = 0
    asset: str = ""
    currency: str = ""
    service: CryptowatchHistoricalPriceService = CryptowatchHistoricalPriceService(
        ts=ts
    )

    def __post_init__(self) -> None:
        self.service.ts = self.ts
