from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.ipfsCID_query import ipfsCID
from telliot_feeds.sources.manual.ipfs_CID_manual_source import ipfsCIDQueryManualSource

url = None

ipfsCID_feed = DataFeed(query=ipfsCID(url=url), source=ipfsCIDQueryManualSource())
