from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator


wrseth_usd_median_feed = DataFeed(
    query=SpotPrice(asset="WRSETH", currency="USD"),
    source=PriceAggregator(
        asset="wrseth",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="wrseth", currency="usd"),
        ],
    ),
)
