from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.sfrax_source import sFRAXSpotPriceSource


sfrax_usd_feed = DataFeed(
    query=SpotPrice(asset="SFRAX", currency="USD"), source=sFRAXSpotPriceSource(asset="sfrax", currency="usd")
)
