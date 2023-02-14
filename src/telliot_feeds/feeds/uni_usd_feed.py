from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coinbase import CoinbaseSpotPriceSource
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.gemini import GeminiSpotPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator

uni_usd_median_feed = DataFeed(
    query=SpotPrice(asset="UNI", currency="USD"),
    source=PriceAggregator(
        asset="uni",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="uni", currency="usd"),
            CoinbaseSpotPriceSource(asset="uni", currency="usd"),
            GeminiSpotPriceSource(asset="uni", currency="usd"),
        ],
    ),
)
