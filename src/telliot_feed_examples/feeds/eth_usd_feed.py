"""Datafeed for current price of ETH in USD used by LegacyQueryReporter."""
from telliot_core.datafeed import DataFeed
from telliot_core.queries import LegacyRequest

from telliot_feed_examples.sources.binance import BinancePriceSource
from telliot_feed_examples.sources.coinbase import CoinbasePriceSource
from telliot_feed_examples.sources.coingecko import CoinGeckoPriceSource
from telliot_feed_examples.sources.kraken import KrakenPriceSource
from telliot_feed_examples.sources.price_aggregator import PriceAggregator

eth_usd_median_feed = DataFeed(
    query=LegacyRequest(legacy_id=1),
    source=PriceAggregator(
        asset="eth",
        currency="usd",
        algorithm="median",
        sources=[
            CoinbasePriceSource(asset="eth", currency="usd"),
            CoinGeckoPriceSource(asset="eth", currency="usd"),
            KrakenPriceSource(asset="eth", currency="usd"),
            BinancePriceSource(asset="eth", currency="usdc"),
            BinancePriceSource(asset="eth", currency="usdt"),
        ],
    ),
)
