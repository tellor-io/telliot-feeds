from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.oeth_source import oethEthSource


oeth_eth_feed = DataFeed(
    query=SpotPrice(asset="OETH", currency="ETH"), source=oethEthSource(asset="oeth", currency="eth")
)
