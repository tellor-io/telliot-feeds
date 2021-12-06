"""Wrapped Ampleforth in USD feed."""
from telliot_core.datafeed import DataFeed
from telliot_core.queries import SpotPrice

from telliot_feed_examples.sources.coingecko import CoinGeckoPriceSource
from telliot_feed_examples.sources.livecoinwatch import LiveCoinWatchPriceSource
from telliot_feed_examples.sources.price_aggregator import PriceAggregator

wampl_usd_median_feed = DataFeed(
    query=SpotPrice(
        asset='wampl',
        currency='usd',
    ),
    source=PriceAggregator(
        asset="wampl",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoPriceSource(asset="wampl", currency="usd"),
            # NomicsPriceSource(asset="wampl", currency="usd"),
            LiveCoinWatchPriceSource(asset="wampl", currency="usd"),
        ],
    ),
)
