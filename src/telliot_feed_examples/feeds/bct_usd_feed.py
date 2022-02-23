from telliot_core.datafeed import DataFeed
from telliot_core.queries import SpotPrice

from telliot_feed_examples.sources.coingecko import CoinGeckoPriceSource
from telliot_feed_examples.sources.nomics import NomicsPriceSource
from telliot_feed_examples.sources.price_aggregator import PriceAggregator

bct_usd_median_feed = DataFeed(
    query=SpotPrice(asset="BCT", currency="USD"),
    source=PriceAggregator(
        asset="bct",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoPriceSource(asset="bct", currency="usd"),
            NomicsPriceSource(asset="bct", currency="usd"),
        ],
    ),
)
