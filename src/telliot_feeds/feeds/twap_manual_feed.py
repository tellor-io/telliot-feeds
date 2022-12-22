import asyncio

from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.twap import TWAP
from telliot_feeds.sources.manual.twap_manual_input_source import TWAPManualSource


# Using defaults to bypass an error handle for auto feeds and unsupported currencies
asset = "eth"
currency = "usd"
timespan = None


twap_manual_feed = DataFeed(
    query=TWAP(asset=asset, currency=currency, timespan=timespan), source=TWAPManualSource()  # type: ignore
)
twap_30d_example_manual_feed = DataFeed(
    query=TWAP(
        asset=asset,
        currency=currency,
        timespan=2592000,  # seconds in 30 days
    ),
    source=TWAPManualSource(),
)


if __name__ == "__main__":
    v, t = asyncio.run(twap_manual_feed.source.fetch_new_datapoint())
