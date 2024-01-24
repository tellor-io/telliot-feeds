from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.string_query import StringQuery
from telliot_feeds.sources.manual.ipfs_CID_manual_source import ipfsCIDQueryManualSource

text = None

ipfsCID_feed = DataFeed(query=StringQuery(text=text), source=ipfsCIDQueryManualSource())
