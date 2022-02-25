"""Datafeed for current price of ETH in JPY used by LegacyQueryReporter."""
from telliot_core.datafeed import DataFeed
from telliot_core.queries import LegacyRequest

from telliot_feed_examples.sources.price.spot.bitfinex import BitfinexSpotPriceSource
from telliot_feed_examples.sources.price.spot.bitflyer import BitflyerSpotPriceSource
from telliot_feed_examples.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feed_examples.sources.price_aggregator import PriceAggregator

eth_jpy_median_feed = DataFeed(
    query=LegacyRequest(legacy_id=59),
    source=PriceAggregator(
        asset="eth",
        currency="jpy",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="eth", currency="jpy"),
            BitflyerSpotPriceSource(asset="eth", currency="jpy"),
            BitfinexSpotPriceSource(asset="eth", currency="jpy"),
        ],
    ),
)
