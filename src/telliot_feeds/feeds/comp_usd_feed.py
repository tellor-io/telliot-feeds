from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coinbase import CoinbaseSpotPriceSource
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.gemini import GeminiSpotPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator

comp_usd_median_feed = DataFeed(
    query=SpotPrice(asset="COMP", currency="USD"),
    source=PriceAggregator(
        asset="comp",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="comp", currency="usd"),
            CoinbaseSpotPriceSource(asset="comp", currency="usd"),
            GeminiSpotPriceSource(asset="comp", currency="usd"),
        ],
    ),
)
