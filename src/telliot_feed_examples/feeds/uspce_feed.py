"""Example datafeed used by USPCEReporter."""
from telliot_feed_examples.datafeed import DataFeed
from telliot_feed_examples.queries.legacy_query import LegacyRequest

from telliot_feed_examples.sources.uspce import USPCESource


uspce_feed = DataFeed(query=LegacyRequest(legacy_id=41), source=USPCESource())
