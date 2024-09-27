from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.gemini import GeminiSpotPriceSource
from telliot_feeds.sources.price.spot.okx import OKXSpotPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator

dot_usd_median_feed = DataFeed(
    query=SpotPrice(asset="DOT", currency="USD"),
    source=PriceAggregator(
        asset="dot",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="dot", currency="usd"),
            GeminiSpotPriceSource(asset="dot", currency="usd"),
            OKXSpotPriceSource(asset="dot", currency="usdt"),
        ],
    ),
)
