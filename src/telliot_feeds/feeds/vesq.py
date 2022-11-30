from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator

vsq_usd_median_feed = DataFeed(
    query=SpotPrice(asset="VSQ", currency="USD"),
    source=PriceAggregator(
        asset="vsq",
        currency="usd",
        algorithm="median",
        sources=[CoinGeckoSpotPriceSource(asset="vsq", currency="usd")],
    ),
)
