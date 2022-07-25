from datetime import datetime
from datetime import time
from typing import Any
from typing import Optional

import pandas as pd

from telliot_feeds.datafeed import DataFeed
from telliot_feeds.dtypes.datapoint import OptionalDataPoint
from telliot_feeds.queries.daily_volatility import DailyVolatility
from telliot_feeds.sources.price.historical.coingecko_daily import CoingeckoDailyHistoricalPriceSource
from telliot_feeds.sources.price.historical.cryptowatch import CryptowatchHistoricalPriceService
from telliot_feeds.sources.price.historical.cryptowatch import CryptowatchHistoricalPriceSource
from telliot_feeds.sources.price.historical.kraken_ohlc import KrakenHistoricalPriceSourceOHLC
from telliot_feeds.sources.price_aggregator import PriceAggregator
from telliot_feeds.utils.log import get_logger

logger = get_logger(__name__)

thirty_days_seconds = 30 * 86400
midnight = datetime.combine(datetime.today(), time.min).timestamp()


async def get_volatility(
    self: Any,
    asset: str,
    currency: str,
    period: int = thirty_days_seconds,
    candle_periods: int = 86400,
    ts: Optional[int] = None,
) -> OptionalDataPoint[float]:

    """Implement PriceServiceInterface

    This implementation gets the historical price from
    the Cryptowatch API using a timestamp. Historical prices are
    fetched from Cryptowatch's recorded Coinbase-pro data.

    Documentation for Cryptowatch API:
    https://docs.cryptowat.ch/rest-api/markets/ohlc
    """
    candles, dt = await self.get_candles(
        asset=asset, currency=currency, ts=ts, period=period, candle_periods=candle_periods
    )
    if candles is not None:
        try:
            if len(candles) == 0:
                logger.warning(f"No candle data from Cryptowatch historical price source for given timestamp: {ts}.")
                return None, None
            df = pd.DataFrame(
                candles,
                columns=["CloseTime", "OpenPrice", "HighPrice", "LowPrice", "ClosePrice", "Volume", "QuoteVolume"],
            )
            volatility = df["ClosePrice"].pct_change().std()

            return float(volatility), dt

        except KeyError as e:
            msg = f"Error parsing Cryptowatch API candle data: KeyError: {e}"
            logger.critical(msg)

    return None, None


CryptowatchHistoricalPriceService.get_price = get_volatility  # type: ignore

eth_usd_30day_volatility = DataFeed(
    query=DailyVolatility(asset="ETH", currency="USD", days=30),
    source=PriceAggregator(
        asset="eth",
        currency="usd",
        algorithm="median",
        sources=[
            CryptowatchHistoricalPriceSource(asset="eth", currency="usd", ts=int(midnight)),
            CoingeckoDailyHistoricalPriceSource(asset="eth", currency="usd", days=30),
            KrakenHistoricalPriceSourceOHLC(asset="eth", currency="usd", ts=int(midnight - thirty_days_seconds)),
        ],
    ),
)
