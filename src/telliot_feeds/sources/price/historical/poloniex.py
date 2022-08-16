from dataclasses import dataclass
from datetime import datetime
from typing import Any
from typing import Optional
from typing import Tuple
from urllib.parse import urlencode

import requests

from telliot_feeds.dtypes.datapoint import datetime_now_utc
from telliot_feeds.dtypes.datapoint import OptionalDataPoint
from telliot_feeds.pricing.price_source import PriceSource
from telliot_feeds.utils.log import get_logger


logger = get_logger(__name__)


# Hardcoded supported asset/currency pairs
# Poloniex swaps the usual order of asset/currency to currency/asset
poloniex_pairs = {"DAI_ETH", "TUSD_ETH", "DAI_BTC", "TUSD_BTC"}


class PoloniexHistoricalPriceService:
    """Poloniex Historical Price Service"""

    def __init__(
        self,
        ts: int = 0,
        timeout: float = 1,
        name: str = "Poloniex Historical Price Service",
        url: str = "https://poloniex.com/",
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

    async def get_trades(
        self,
        asset: str,
        currency: str,
        period: int = 900,  # 15 minutes
        ts: Optional[int] = None,
    ) -> Tuple[Optional[list[Any]], Optional[datetime]]:
        """Returns trade data found within a given period.
        The period's middle is at the given timestamp."""
        if ts is None:
            ts = self.ts

        asset = asset.upper()
        currency = currency.upper()
        pair = currency + "_" + asset  # Poloniex wants the reverse of standard order: asset/currency

        if pair not in poloniex_pairs:
            raise Exception(f"Currency pair not supported: {pair}")

        url_params = urlencode(
            {
                "currencyPair": pair,
                "start": int(ts - period),
                "end": ts,
            }
        )

        # Source: https://docs.poloniex.com/#returntradehistory-public
        request_url = f"public?command=returnTradeHistory&{url_params}"

        d = self.get_url(request_url)
        trades = []

        if "error" in str(d):
            logger.error(d)
            return None, None

        elif "response" in d:
            rsp = d["response"]
            if isinstance(rsp, list):
                trades = rsp
            else:
                logger.error(f"Unexpected response type: {type(rsp)}")
                return None, None
        else:
            raise Exception("Invalid response from get_url")

        return trades, datetime_now_utc()

    async def get_price(
        self,
        asset: str,
        currency: str,
        period: int = 20000,
        ts: Optional[int] = None,
    ) -> OptionalDataPoint[float]:
        """Implement PriceServiceInterface

        This implementation gets the historical price from
        the Poloniex API using a timestamp."""
        trades, dt = await self.get_trades(asset=asset, currency=currency, ts=ts, period=period)

        if trades is not None:
            try:
                if len(trades) == 0:
                    logger.warning(f"No data from Poloniex historical price source for given timestamp: {ts}.")
                    return None, None

                # Price from last trade in period
                return float(trades[-1]["rate"]), dt

            except KeyError as e:
                msg = f"Error parsing Poloniex API response: KeyError: {e}"
                logger.critical(msg)

        return None, None


@dataclass
class PoloniexHistoricalPriceSource(PriceSource):
    ts: int = 0
    asset: str = ""
    currency: str = ""
    service: PoloniexHistoricalPriceService = PoloniexHistoricalPriceService(ts=ts)  # type: ignore

    def __post_init__(self) -> None:
        self.service.ts = self.ts
