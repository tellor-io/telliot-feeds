"""Example datafeed used by PLSUSDReporter."""
from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.pulsechain_subgraph import PulsechainSubgraphSource

pls_usd_feed = DataFeed(
    query=SpotPrice(asset="pls", currency="usd"), source=PulsechainSubgraphSource(asset="pls", currency="usd")
)
