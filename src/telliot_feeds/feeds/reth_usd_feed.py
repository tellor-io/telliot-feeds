from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.reth_source import RethSpotPriceSource

reth_usd_median_feed = DataFeed(
    query=SpotPrice(asset="RETH", currency="USD"),
    source=RethSpotPriceSource(asset="reth", currency="usd"),
)
