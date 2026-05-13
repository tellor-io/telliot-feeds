from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.susde_fundamental_source import sUSDESpotPriceSource


susde_usd_median_feed = DataFeed(
    query=SpotPrice(asset="sUSDe", currency="USD"),
    source=sUSDESpotPriceSource(asset="susde", currency="usd"),
)
