from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coinbase import CoinbaseSpotPriceSource
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.gemini import GeminiSpotPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator

ltc_usd_median_feed = DataFeed(
    query=SpotPrice(asset="LTC", currency="USD"),
    source=PriceAggregator(
        asset="ltc",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="ltc", currency="usd"),
            CoinbaseSpotPriceSource(asset="ltc", currency="usd"),
            GeminiSpotPriceSource(asset="ltc", currency="usd"),
        ],
    ),
)
