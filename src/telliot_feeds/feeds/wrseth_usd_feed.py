from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.wrseth_source import wrsETHSpotPriceSource


wrseth_usd_feed = DataFeed(
    query=SpotPrice(asset="WRSETH", currency="USD"), source=wrsETHSpotPriceSource(asset="wrseth", currency="usd")
)
