from telliot_core.datafeed import DataFeed
from telliot_core.queries import SpotPrice
from telliot_core.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_core.sources.price_aggregator import PriceAggregator

vsq_usd_median_feed = DataFeed(
    query=SpotPrice(asset="VSQ", currency="USD"),
    source=PriceAggregator(
        asset="vsq",
        currency="usd",
        algorithm="median",
        sources=[CoinGeckoSpotPriceSource(asset="vsq", currency="usd")],
    ),
)
