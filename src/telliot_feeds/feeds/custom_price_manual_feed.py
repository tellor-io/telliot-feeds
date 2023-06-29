from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.custom_price import CustomPrice
from telliot_feeds.sources.manual.spot_price_input_source import SpotPriceManualSource


# Using dummy defaults to bypass an error handle for feeds w/out non-manual sources
identifier: str = "landx"
asset: str = "corn"
currency: str = "usd"
unit: str = "per_kilogram"


custom_price_manual_feed = DataFeed(
    query=CustomPrice(identifier=identifier, asset=asset, currency=currency, unit=unit), source=SpotPriceManualSource()
)
