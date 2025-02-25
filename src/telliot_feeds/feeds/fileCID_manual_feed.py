from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.fileCID import FileCIDQuery
from telliot_feeds.sources.manual.fileCID_manual_source import fileCIDManualSource

url = None

fileCID_manual_feed = DataFeed(query=FileCIDQuery(url=url), source=fileCIDManualSource())
filecid_example_feed = DataFeed(
    query=FileCIDQuery(url="https://raw.githubusercontent.com/tellor-io/dataSpecs/main/README.md"),
    source=fileCIDManualSource(),
)
