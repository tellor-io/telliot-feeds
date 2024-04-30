from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.fileCID import FileCID
from telliot_feeds.sources.manual.fileCID_manual_source import fileCIDManualSource

url = None

fileCID_manual_feed = DataFeed(query=FileCID(url=url), source=fileCIDManualSource())
