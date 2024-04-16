from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.wusdm_source import wUSDMSpotPriceSource


leth_usd_feed = DataFeed(
    query=SpotPrice(asset="LETH", currency="USD"), source=wUSDMSpotPriceSource(asset="leth", currency="usd")
)
