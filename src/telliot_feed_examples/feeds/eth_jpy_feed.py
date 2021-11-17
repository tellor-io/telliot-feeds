"""Datafeed for current price of ETH in JPY used by LegacyQueryReporter."""
from telliot_core.datafeed import DataFeed
from telliot_core.queries import LegacyRequest

from telliot_feed_examples.sources.bitfinex import BitfinexPriceSource
from telliot_feed_examples.sources.bitflyer import BitflyerPriceSource
from telliot_feed_examples.sources.coingecko import CoinGeckoPriceSource
from telliot_feed_examples.sources.price_aggregator import PriceAggregator

eth_jpy_median_feed = DataFeed(
    query=LegacyRequest(legacy_id=59),
    source=PriceAggregator(
        asset="eth",
        currency="jpy",
        algorithm="median",
        sources=[
            CoinGeckoPriceSource(asset="eth", currency="jpy"),
            BitflyerPriceSource(asset="eth", currency="jpy"),
            BitfinexPriceSource(asset="eth", currency="jpy"),
        ],
    ),
)
