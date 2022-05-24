from telliot_core.datafeed import DataFeed
from telliot_core.queries import SpotPrice
from telliot_core.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_core.sources.price_aggregator import PriceAggregator

ohm_eth_median_feed = DataFeed(
    query=SpotPrice(asset="OHM", currency="ETH"),
    source=PriceAggregator(
        asset="ohm",
        currency="eth",
        algorithm="median",
        sources=[CoinGeckoSpotPriceSource(asset="ohm", currency="eth")],
    ),
)
