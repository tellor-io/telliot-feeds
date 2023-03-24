from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.wsteth_source import CustomWstETHSpotPriceSource

wsteth_usd_median_feed = DataFeed(
    query=SpotPrice(asset="WSTETH", currency="USD"), source=CustomWstETHSpotPriceSource(asset="wsteth", currency="usd")
)
