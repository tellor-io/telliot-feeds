from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.pulsex_subgraph import PulseXSupgraphSource
from telliot_feeds.sources.price_aggregator import PriceAggregator

hex_usd_median_feed = DataFeed(
    query=SpotPrice(asset="HEX", currency="USD"),
    source=PriceAggregator(
        asset="hex",
        currency="usd",
        algorithm="median",
        sources=[
            PulseXSupgraphSource(asset="hex", currency="usd"),
        ],
    ),
)