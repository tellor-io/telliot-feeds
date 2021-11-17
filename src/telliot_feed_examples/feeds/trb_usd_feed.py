"""Datafeed for current price of TRB in USD used by LegacyQueryReporter."""
from telliot_core.datafeed import DataFeed
from telliot_core.queries import LegacyRequest

from telliot_feed_examples.sources.coingecko import CoinGeckoPriceSource
from telliot_feed_examples.sources.price_aggregator import PriceAggregator

trb_usd_median_feed = DataFeed(
    query=LegacyRequest(legacy_id=50),
    source=PriceAggregator(
        asset="trb",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoPriceSource(asset="trb", currency="usd"),
        ],
    ),
)
