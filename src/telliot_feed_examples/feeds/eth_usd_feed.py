"""Datafeed for current price of ETH in USD used by LegacyQueryReporter."""
from telliot_core.datafeed import DataFeed
from telliot_core.queries import LegacyRequest

from telliot_feed_examples.sources.price.spot.binance import BinanceSpotPriceSource
from telliot_feed_examples.sources.price.spot.coinbase import CoinbaseSpotPriceSource
from telliot_feed_examples.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feed_examples.sources.price.spot.kraken import KrakenSpotPriceSource
from telliot_feed_examples.sources.price_aggregator import PriceAggregator

eth_usd_median_feed = DataFeed(
    query=LegacyRequest(legacy_id=1),
    source=PriceAggregator(
        asset="eth",
        currency="usd",
        algorithm="median",
        sources=[
            CoinbaseSpotPriceSource(asset="eth", currency="usd"),
            CoinGeckoSpotPriceSource(asset="eth", currency="usd"),
            KrakenSpotPriceSource(asset="eth", currency="usd"),
            BinanceSpotPriceSource(asset="eth", currency="usdc"),
            BinanceSpotPriceSource(asset="eth", currency="usdt"),
        ],
    ),
)
