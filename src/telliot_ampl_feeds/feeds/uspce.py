"""Example datafeed used by USPCEReporter."""
from telliot.datafeed import DataFeed
from telliot.queries.legacy_query import LegacyRequest

from telliot_ampl_feeds.sources.uspce import USPCESource


uspce_feed = DataFeed(
    query=LegacyRequest(legacy_id=10), source=USPCESource()
)
