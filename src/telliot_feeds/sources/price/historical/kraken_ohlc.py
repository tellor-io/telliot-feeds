from dataclasses import dataclass
from typing import Any
from typing import Optional
from urllib.parse import urlencode

import pandas as pd

from telliot_feeds.pricing.price_source import PriceSource
from telliot_feeds.utils.log import get_logger
from telliot_feeds.sources.price.historical.kraken import KrakenHistoricalPriceService

logger = get_logger(__name__)


# Hardcoded supported assets & currencies
# Kraken uses XBT instead of BTC for its APIs:
# https://support.kraken.com/hc/en-us/articles/360001206766-Bitcoin-currency-code-XBT-vs-BTC
kraken_assets = {"ETH", "XBT"}
kraken_currencies = {"USD"}


class KrakenHistoricalPriceServiceOHLC(KrakenHistoricalPriceService):

    def get_request_url(self, asset: str, currency: str, period_start: int) -> str:
        """Assemble Kraken historical trades request url."""
        asset = asset.upper()
        currency = currency.upper()

        if asset not in kraken_assets:
            raise Exception(f"Asset not supported: {asset}")
        if currency not in kraken_currencies:
            raise Exception(f"Currency not supported: {currency}")

        url_params = urlencode({"pair": f"{asset}{currency}", "since": period_start, "interval": 1440})
        # Source: https://docs.kraken.com/rest/#operation/getRecentTrades
        return f"/0/public/OHLC?{url_params}"

    def resp_price_parse(self, asset: str, currency: str, resp: dict[Any, Any]) -> Optional[float]:
        """Gets first price from trades data."""
        try:
            # Price of last trade in trades list retrieved from API
            pair_key = f"X{asset.upper()}Z{currency.upper()}"
            data = resp["result"][pair_key]
            df = pd.DataFrame(data, columns=["CloseTime", "Open", "High", "Low", "Close", "?", "V", "QV"])
            df["Close"] = df["Close"].astype(float)
            volatility = df["Close"].pct_change().std()
        except KeyError as e:
            msg = f"Error parsing Kraken API response: KeyError: {e}"
            logger.critical(msg)
            return None

        if len(data) == 0:
            logger.warning("No trades found.")
            return None
        return float(volatility)


@dataclass
class KrakenHistoricalPriceSourceOHLC(PriceSource):
    ts: int = 0
    asset: str = ""
    currency: str = ""
    service: KrakenHistoricalPriceServiceOHLC = KrakenHistoricalPriceServiceOHLC(ts=ts)

    def __post_init__(self) -> None:
        self.service.ts = self.ts
