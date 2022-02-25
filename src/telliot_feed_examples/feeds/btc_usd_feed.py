"""Example datafeed used by BTCUSDReporter."""
from telliot_core.datafeed import DataFeed
from telliot_core.queries.legacy_query import LegacyRequest

from telliot_feed_examples.sources.price.spot.bittrex import BittrexSpotPriceSource
from telliot_feed_examples.sources.price.spot.coinbase import CoinbaseSpotPriceSource
from telliot_feed_examples.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feed_examples.sources.price.spot.gemini import GeminiSpotPriceSource
from telliot_feed_examples.sources.price_aggregator import PriceAggregator

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
