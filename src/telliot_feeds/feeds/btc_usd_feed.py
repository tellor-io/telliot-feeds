"""Example datafeed used by BTCUSDReporter."""
from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.legacy_query import LegacyRequest
from telliot_feeds.sources.price.spot.bittrex import BittrexSpotPriceSource
from telliot_feeds.sources.price.spot.coinbase import CoinbaseSpotPriceSource
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.gemini import GeminiSpotPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator

btc_usd_median_feed = DataFeed(
    query=LegacyRequest(legacy_id=2),
    source=PriceAggregator(
        asset="btc",
        currency="usd",
        algorithm="median",
        sources=[
            CoinbaseSpotPriceSource(asset="btc", currency="usd"),
            CoinGeckoSpotPriceSource(asset="btc", currency="usd"),
            BittrexSpotPriceSource(asset="btc", currency="usd"),
            GeminiSpotPriceSource(asset="btc", currency="usd"),
        ],
    ),
)
