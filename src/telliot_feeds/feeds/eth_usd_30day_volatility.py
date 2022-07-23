from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.daily_volatility import DailyVolatility
from telliot_feeds.sources.price.historical.coingecko_daily import CoingeckoDailyHistoricalPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator


eth_usd_30day_volatility = DataFeed(
    query=DailyVolatility(asset="ETH", currency="USD", days=30),
    source=PriceAggregator(
        asset="eth",
        currency="usd",
        algorithm="median",
        sources=[CoingeckoDailyHistoricalPriceSource(asset="eth", currency="usd", days=30)],
    ),
)
