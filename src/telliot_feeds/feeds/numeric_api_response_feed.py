"""Datafeed for reporting responses to the NumericApiResponse query type.

More info:
https://github.com/tellor-io/dataSpecs/blob/main/types/NumericApiResponse.md

 """
from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.numeric_api_response_query import NumericApiResponse
from telliot_feeds.sources.numeric_api_response import NumericApiResponseSource

url = None
parseStr = None

numeric_api_response_feed = DataFeed(
    query=NumericApiResponse(url=url, parseStr=parseStr),
    source=NumericApiResponseSource(url=url, parseStr=parseStr),
)
