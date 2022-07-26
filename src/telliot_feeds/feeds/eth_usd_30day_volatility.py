from datetime import datetime
from datetime import time
from typing import Callable

from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.daily_volatility import DailyVolatility
from telliot_feeds.sources.price.historical.coingecko_daily import CoingeckoDailyHistoricalPriceSource
from telliot_feeds.sources.price.historical.cryptowatch_ohlc import CryptowatchHistoricalOHLCPriceSource
from telliot_feeds.sources.price.historical.kraken_ohlc import KrakenHistoricalPriceSourceOHLC
from telliot_feeds.sources.price_aggregator import PriceAggregator
from telliot_feeds.utils.log import get_logger

logger = get_logger(__name__)

thirty_days_seconds = 30 * 86400
midnight: Callable[[], float] = lambda: datetime.combine(datetime.today(), time.min).timestamp()


eth_usd_30day_volatility = DataFeed(
    query=DailyVolatility(asset="ETH", currency="USD", days=30),
    source=PriceAggregator(
        asset="eth",
        currency="usd",
        algorithm="median",
        sources=[
            CryptowatchHistoricalOHLCPriceSource(
                asset="eth", currency="usd", ts=int(midnight())
            ),  # get data before midnight
            CoingeckoDailyHistoricalPriceSource(asset="eth", currency="usd", days=29),
            KrakenHistoricalPriceSourceOHLC(
                asset="eth", currency="usd", ts=int(midnight() - thirty_days_seconds)
            ),  # get data since 30 days ago
        ],
    ),
)
