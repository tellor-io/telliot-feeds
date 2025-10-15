from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.yeth_source import yETHSpotPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator

yeth_usd_median_feed = DataFeed(
    query=SpotPrice(asset="yeth", currency="USD"),
    source=PriceAggregator(
        asset="yeth",
        currency="usd",
        algorithm="median",
        sources=[
            yETHSpotPriceSource(asset="yeth", currency="usd"),
        ],
    ),
)
