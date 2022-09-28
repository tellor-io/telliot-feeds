"""Example datafeed used by USPCEReporter."""
from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.ampleforth.uspce import USPCE
from telliot_feeds.sources.uspce import USPCESource


uspce_feed = DataFeed(query=USPCE(), source=USPCESource())
