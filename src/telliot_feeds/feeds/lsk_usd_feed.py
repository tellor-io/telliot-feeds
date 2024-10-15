from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.kraken import KrakenSpotPriceSource
from telliot_feeds.sources.price.spot.okx import OKXSpotPriceSource
from telliot_feeds.sources.price.spot.uniswapV3 import UniswapV3PriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator

lsk_usd_median_feed = DataFeed(
    query=SpotPrice(asset="LSK", currency="USD"),
    source=PriceAggregator(
        asset="lsk",
        currency="usd",
        algorithm="median",
        sources=[
            OKXSpotPriceSource(asset="lsk", currency="usdt"),
            KrakenSpotPriceSource(asset="lsk", currency="usd"),
            UniswapV3PriceSource(asset="lsk", currency="usd"),
        ],
    ),
)
