from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.pulsex_subgraph import PulseXSupgraphSource
from telliot_feeds.sources.price_aggregator import PriceAggregator

inc_usd_median_feed = DataFeed(
    query=SpotPrice(asset="INC", currency="USD"),
    source=PriceAggregator(
        asset="INC",
        currency="usd",
        algorithm="median",
        sources=[
	    PulseXSupgraphSource(asset="inc", currency="usd"),
        ],
    ),
)