"""Example datafeed used by USPCEReporter."""
from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.ampleforth.uspce import AmpleforthUSPCE
from telliot_feeds.sources.manual.uspce import USPCESource


uspce_feed = DataFeed(query=AmpleforthUSPCE(), source=USPCESource())
