from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.legacy_query import LegacyRequest
from telliot_feeds.sources.manual_sources.spot_price_input_source import SpotPriceManualSource


legacy_id = None


legacy_request_manual_feed = DataFeed(
    query=LegacyRequest(legacy_id=legacy_id), source=SpotPriceManualSource()  # type: ignore
)
