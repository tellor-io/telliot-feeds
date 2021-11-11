"""Example datafeed used by USPCEReporter."""
from telliot_core.datafeed import DataFeed
from telliot_core.queries.legacy_query import LegacyRequest

from telliot_ampl_feeds.sources.uspce import USPCESource


uspce_feed = DataFeed(query=LegacyRequest(legacy_id=10), source=USPCESource())
