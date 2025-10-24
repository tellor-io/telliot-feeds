from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.susn_contract_source import sUSNSpotPriceSource


susn_usd_feed = DataFeed(
    query=SpotPrice(asset="SUSN", currency="USD"), source=sUSNSpotPriceSource(asset="susn", currency="usd")
)
