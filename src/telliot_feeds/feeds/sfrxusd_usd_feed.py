from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.sfrxusd_source import sfrxUSDSpotPriceSource


sfrxusd_usd_feed = DataFeed(
    query=SpotPrice(asset="SFRXUSD", currency="USD"), source=sfrxUSDSpotPriceSource(asset="sfrxusd", currency="usd")
)
