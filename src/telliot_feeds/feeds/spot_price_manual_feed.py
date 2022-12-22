from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.manual.spot_price_input_source import SpotPriceManualSource

# Using defaults to bypass an error handle for feeds w/out non-manual sources
asset: str = "eth"
currency: str = "usd"


spot_price_manual_feed = DataFeed(query=SpotPrice(asset=asset, currency=currency), source=SpotPriceManualSource())
