from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.atla_source import atlaMockSource

# returns a price of $1 for ATLA (which hasn't launched yet)
atla_helper_feed = DataFeed(
    query=SpotPrice(asset="ATLA", currency="USD"),
    source=atlaMockSource(
        asset="atla",
        currency="usd",
    ),
)
