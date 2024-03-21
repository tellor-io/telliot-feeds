from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator


meth_usd_median_feed = DataFeed(
    query=SpotPrice(asset="LETH", currency="USD"),
    source=PriceAggregator(
        asset="leth",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="leth", currency="usd"),
        ],
    ),
)