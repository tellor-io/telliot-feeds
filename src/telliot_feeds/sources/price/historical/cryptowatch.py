from dataclasses import dataclass
from datetime import datetime
from typing import Any
from typing import Optional
from typing import Tuple
from urllib.parse import urlencode

import requests

from telliot_feeds.dtypes.datapoint import datetime_now_utc
from telliot_feeds.dtypes.datapoint import OptionalDataPoint
from telliot_feeds.pricing.price_service import WebPriceService
from telliot_feeds.pricing.price_source import PriceSource
from telliot_feeds.utils.log import get_logger


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

    async def get_candles(
        self,
        asset: str,
        currency: str,
        candle_periods: int = 60,  # 1 minute
        period: int = 900,  # 15 minutes
        ts: Optional[int] = None,
    ) -> Tuple[Optional[list[Any]], Optional[datetime]]:
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

        url_params = urlencode(
            {
                "after": int(ts - period),
                "before": ts,
                "periods": candle_periods,
            }
        )

        request_url = f"markets/coinbase-pro/{pair}/ohlc?{url_params}"

        d = self.get_url(request_url)
        candles = None

        if "error" in d:
            logger.error(d)
            return None, None

        elif "response" in d:
            response = d["response"]

            try:
                candles = response["result"][str(candle_periods)]
            except KeyError as e:
                msg = f"Error parsing Cryptowatch API response: KeyError: {e}"
                logger.critical(msg)

        else:
            raise Exception("Invalid response from get_url")

        return candles, datetime_now_utc()

    async def get_price(
        self, asset: str, currency: str, period: int = 10000, ts: Optional[int] = None
    ) -> OptionalDataPoint[float]:
        """Implement PriceServiceInterface

        This implementation gets the historical price from
        the Cryptowatch API using a timestamp. Historical prices are
        fetched from Cryptowatch's recorded Coinbase-pro data.

        Documentation for Cryptowatch API:
        https://docs.cryptowat.ch/rest-api/markets/ohlc
        """
        candles, dt = await self.get_candles(asset=asset, currency=currency, ts=ts, period=period)

        if candles is not None:
            try:
                if len(candles) == 0:
                    logger.warning(
                        f"No candle data from Cryptowatch historical price source for given timestamp: {ts}."
                    )
                    return None, None

                # Price from last candle in period
                return float(candles[-1][4]), dt

            except KeyError as e:
                msg = f"Error parsing Cryptowatch API candle data: KeyError: {e}"
                logger.critical(msg)

        return None, None


@dataclass
class CryptowatchHistoricalPriceSource(PriceSource):
    ts: int = 0
    asset: str = ""
    currency: str = ""
    service: CryptowatchHistoricalPriceService = CryptowatchHistoricalPriceService(ts=ts)

    def __post_init__(self) -> None:
        self.service.ts = self.ts
