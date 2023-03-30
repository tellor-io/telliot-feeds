from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.wsteth_source import WstETHSpotPriceSource

wsteth_usd_median_feed = DataFeed(
    query=SpotPrice(asset="WSTETH", currency="USD"), source=WstETHSpotPriceSource(asset="wsteth", currency="usd")
)

wsteth_eth_median_feed = DataFeed(
    query=SpotPrice(asset="WSTETH", currency="ETH"), source=WstETHSpotPriceSource(asset="wsteth", currency="eth")
)
