from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator


yusd_usd_median_feed = DataFeed(
    query=SpotPrice(asset="yusd", currency="USD"),
    source=PriceAggregator(
        asset="yusd",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="yusd", currency="usd"),
        ],
    ),
)
