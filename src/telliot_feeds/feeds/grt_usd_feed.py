from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.gemini import GeminiSpotPriceSource
from telliot_feeds.sources.price.spot.okx import OKXSpotPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator

grt_usd_median_feed = DataFeed(
    query=SpotPrice(asset="GRT", currency="USD"),
    source=PriceAggregator(
        asset="grt",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="grt", currency="usd"),
            GeminiSpotPriceSource(asset="grt", currency="usd"),
            OKXSpotPriceSource(asset="grt", currency="usdt"),
        ],
    ),
)
