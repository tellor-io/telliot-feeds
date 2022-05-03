from telliot_core.datafeed import DataFeed
from telliot_core.queries.api_query import APIQuery

from telliot_feed_examples.sources.api_source import APIQuerySource

# example API call to random API

# to do a specific one, a unique feed example can be made


api_url_feed = DataFeed(
    query=APIQuery(
        api_url="https://www.boredapi.com/api/activity", arg_string="activity, link"
    ),
    source=APIQuerySource(
        url="https://www.boredapi.com/api/activity", arg_string="activity, link"
    ),
)
