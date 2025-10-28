from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.yusd_contract_source import yUSDSpotPriceSource


yusd_usd_feed = DataFeed(
    query=SpotPrice(asset="yUSD", currency="USD"), source=yUSDSpotPriceSource(asset="yusd", currency="usd")
)
