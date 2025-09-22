from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.vyusd_source import vyUSDSpotPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator

vyusd_usd_median_feed = DataFeed(
    query=SpotPrice(asset="vyUSD", currency="USD"),
    source=PriceAggregator(
        asset="vyusd",
        currency="usd",
        algorithm="median",
        sources=[
            vyUSDSpotPriceSource(asset="vyusd", currency="usd"),
        ],
    ),
)
