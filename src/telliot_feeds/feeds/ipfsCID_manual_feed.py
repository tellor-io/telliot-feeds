from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.ipfsCID_query import ipfsCID_query
from telliot_feeds.sources.manual.ipfs_CID_manual_source import ipfsCIDQueryManualSource

text = None

ipfsCID_feed = DataFeed(query=ipfsCID_query(text=text), source=ipfsCIDQueryManualSource())
