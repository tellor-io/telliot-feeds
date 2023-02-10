from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coinbase import CoinbaseSpotPriceSource
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.gemini import GeminiSpotPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator

doge_usd_median_feed = DataFeed(
    query=SpotPrice(asset="DOGE", currency="USD"),
    source=PriceAggregator(
        asset="doge",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="doge", currency="usd"),
            CoinbaseSpotPriceSource(asset="doge", currency="usd"),
            GeminiSpotPriceSource(asset="doge", currency="usd"),
        ],
    ),
)
