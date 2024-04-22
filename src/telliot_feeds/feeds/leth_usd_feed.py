from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.leth_source import LETHSpotPriceSource


leth_usd_feed = DataFeed(
    query=SpotPrice(asset="LETH", currency="USD"), source=LETHSpotPriceSource(asset="leth", currency="usd")
)
