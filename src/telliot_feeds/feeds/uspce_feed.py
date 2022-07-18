"""Example datafeed used by USPCEReporter."""
from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.legacy_query import LegacyRequest
from telliot_feeds.sources.uspce import USPCESource


uspce_feed = DataFeed(query=LegacyRequest(legacy_id=41), source=USPCESource())
