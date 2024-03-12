from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.wusdm_source import wUSDMSpotPriceSource


wusdm_usd_feed = DataFeed(
    query=SpotPrice(asset="WUSDM", currency="USD"), source=wUSDMSpotPriceSource(asset="wusdm", currency="usd")
)
