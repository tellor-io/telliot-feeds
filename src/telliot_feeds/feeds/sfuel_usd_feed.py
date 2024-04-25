from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.sfuel_source import sFuelSpotPriceSource


sfuel_usd_feed = DataFeed(
    query=SpotPrice(asset="SFUEL", currency="USD"),
    source=sFuelSpotPriceSource(
        asset="sfuel",
        currency="usd",
    ),
)
