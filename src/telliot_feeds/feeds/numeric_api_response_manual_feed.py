from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.numeric_api_response_query import NumericApiResponse
from telliot_feeds.sources.manual.numeric_api_manual_response import NumericApiManualResponse


url = None
parse_str = None

numeric_api_response_manual_feed = DataFeed(
    query=NumericApiResponse(url=url, parseStr=parse_str), source=NumericApiManualResponse()
)
