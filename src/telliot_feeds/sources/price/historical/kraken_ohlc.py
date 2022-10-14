from dataclasses import dataclass
from typing import Any
from typing import Optional
from urllib.parse import urlencode

from telliot_feeds.pricing.price_source import PriceSource
from telliot_feeds.sources.price.historical.kraken import KrakenHistoricalPriceService
from telliot_feeds.utils.log import get_logger
from telliot_feeds.utils.stdev_calculator import stdev_calculator

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
            logger.warning(f"Asset not supported: {asset}")
        if currency not in kraken_currencies:
            logger.warning(f"Currency not supported: {currency}")

        url_params = urlencode({"pair": f"{asset}{currency}", "since": period_start, "interval": 1440})
        # Source: https://docs.kraken.com/rest/#operation/getRecentTrades
        return f"/0/public/OHLC?{url_params}"

    def resp_price_parse(self, asset: str, currency: str, resp: dict[Any, Any]) -> Optional[float]:
        """Gets OHLC prices from Kraken API"""
        try:
            # OHLC prices for last thrity days
            pair_key = f"X{asset.upper()}Z{currency.upper()}"
            try:
                data = resp["result"][pair_key]
                if len(data) < 30:
                    logger.warning("Not enough data to calculate volatility")
                    return None
            except KeyError as e:
                msg = f"Error parsing Kraken API response: KeyError: {e}"
                logger.error(msg)
                return None
            close_prices = [float(i[4]) for i in data]
            volatility = stdev_calculator(close_prices)
        except Exception as e:
            logger.error(e)
            return None
        return volatility


@dataclass
class KrakenHistoricalPriceSourceOHLC(PriceSource):
    ts: int = 0
    asset: str = ""
    currency: str = ""
    service: KrakenHistoricalPriceServiceOHLC = KrakenHistoricalPriceServiceOHLC(ts=ts)

    def __post_init__(self) -> None:
        self.service.ts = self.ts
