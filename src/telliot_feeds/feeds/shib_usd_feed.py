from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coinbase import CoinbaseSpotPriceSource
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.gemini import GeminiSpotPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator

shib_usd_median_feed = DataFeed(
    query=SpotPrice(asset="SHIB", currency="USD"),
    source=PriceAggregator(
        asset="shib",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="shib", currency="usd"),
            CoinbaseSpotPriceSource(asset="shib", currency="usd"),
            GeminiSpotPriceSource(asset="shib", currency="usd"),
        ],
    ),
)
