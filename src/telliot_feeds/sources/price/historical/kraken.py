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

    def get_request_url(self, asset: str, currency: str, period_start: int) -> str:
        """Assemble Kraken historical trades request url."""
        asset = asset.upper()
        currency = currency.upper()

        if asset not in kraken_assets:
            logger.warning(f"Asset not supported: {asset}")
        if currency not in kraken_currencies:
            logger.warning(f"Currency not supported: {currency}")

        url_params = urlencode({"pair": f"{asset}{currency}", "since": period_start})  # Unix timestamp

        # Source: https://docs.kraken.com/rest/#operation/getRecentTrades
        return f"/0/public/Trades?{url_params}"

    def resp_price_parse(self, asset: str, currency: str, resp: dict[Any, Any]) -> Optional[float]:
        """Gets first price from trades data."""
        try:
            # Price of last trade in trades list retrieved from API
            pair_key = f"X{asset.upper()}Z{currency.upper()}"
            trades = resp["result"][pair_key]
        except KeyError as e:
            msg = f"Error parsing Kraken API response: KeyError: {e}"
            logger.critical(msg)
            return None

        if len(trades) == 0:
            logger.warning("No trades found.")
            return None

        return float(trades[-1][0])

    def resp_all_trades_parse(self, asset: str, currency: str, resp: dict[Any, Any]) -> Optional[list[str]]:
        """Gets all trades."""
        trades = None
        try:
            pair_key = f"X{asset.upper()}Z{currency.upper()}"
            trades = resp["result"][pair_key]
        except KeyError as e:
            msg = f"Error parsing Kraken API response: KeyError: {e}"
            logger.critical(msg)

        return trades

    async def get_price(self, asset: str, currency: str, ts: Optional[int] = None) -> OptionalDataPoint[float]:
        """Implement PriceServiceInterface

        This implementation gets the historical price from
        the Kraken API using a timestamp."""
        if ts is None:
            ts = self.ts

        # fetch trades data for a minute before expiry,
        # if no trades found, then fetch trades for 2 minutes before expiry, etc.
        # break after checking fifteen minutes before expiry
        for i in range(15):
            period = 60 * (i + 1)
            trades, dt = await self.get_trades(asset, currency, period, ts)
            if not trades:
                continue
            price = float(trades[-1][0])
            logger.info(f"Price found up to {i+1} min before expiry: {price}")
            return price, dt

        logger.info("No trades found up to 15 minutes before expiry.")
        return None, None

    async def get_trades(
        self,
        asset: str,
        currency: str,
        period: int = 900,  # 15 minutes
        ts: Optional[int] = None,
    ) -> Tuple[Optional[list[str]], Optional[datetime]]:
        """Retrieves list of historical prices.

        Gets historical prices of trades data from Kraken API using a timestamp.
        Returns all trades data within the given period. The period is moved backwards
        in time if current time overlaps.

        Args:
            period: time window in seconds of retrieved trades
            timestamp: unix timestamp, beginning of
            the period (time window of fetched trades data)

        Returns:
            trades: list of trades (sublists). The elements of a trade
            sublist (in order) are price, volume, time, buy/sell, market/limit,
            and miscellaneous."""

        if ts is None:
            ts = self.ts

        period_start = int(ts - period)

        req_url = self.get_request_url(asset, currency, period_start)

        d = self.get_url(req_url)

        if "error" in d:
            logger.error(d)
            return None, None

        elif "response" in d:
            response = d["response"]
            trades = self.resp_all_trades_parse(resp=response, asset=asset, currency=currency)
            return trades, datetime_now_utc()
        else:
            raise Exception("Invalid response from get_url")

        return trades, datetime_now_utc()


@dataclass
class KrakenHistoricalPriceSource(PriceSource):
    ts: int = 0
    asset: str = ""
    currency: str = ""
    service: KrakenHistoricalPriceService = KrakenHistoricalPriceService(ts=ts)

    def __post_init__(self) -> None:
        self.service.ts = self.ts
