from telliot_core.datafeed import DataFeed
from telliot_core.queries import SpotPrice

from telliot_feed_examples.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feed_examples.sources.price.spot.nomics import NomicsSpotPriceSource
from telliot_feed_examples.sources.price_aggregator import PriceAggregator

ric_usd_median_feed = DataFeed(
    query=SpotPrice(asset="RIC", currency="USD"),
    source=PriceAggregator(
        asset="ric",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="ric", currency="usd"),
            NomicsSpotPriceSource(asset="ric", currency="usd"),
        ],
    ),
)
