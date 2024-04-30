from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.sfuel_source import sFuelMockSource

# returns a price of $1 for sFUEL (even though it's free)
sfuel_helper_feed = DataFeed(
    query=SpotPrice(asset="SFUEL", currency="USD"),
    source=sFuelMockSource(
        asset="sfuel",
        currency="usd",
    ),
)
