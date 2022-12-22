from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.string_query import StringQuery
from telliot_feeds.sources.manual.string_query_manual_source import StringQueryManualSource

text = None

string_query_feed = DataFeed(query=StringQuery(text=text), source=StringQueryManualSource())
