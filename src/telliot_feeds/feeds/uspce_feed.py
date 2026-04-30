"""Example datafeed used by USPCEReporter."""
from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.ampleforth.uspce import AmpleforthUSPCE
from telliot_feeds.sources.bea_gov import BEAPCESource


uspce_feed = DataFeed(query=AmpleforthUSPCE(), source=BEAPCESource())
