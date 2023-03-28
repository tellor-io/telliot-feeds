from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coinbase import CoinbaseSpotPriceSource
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator

op_usd_median_feed = DataFeed(
    query=SpotPrice(asset="OP", currency="USD"),
    source=PriceAggregator(
        asset="op",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="op", currency="usd"),
            CoinbaseSpotPriceSource(asset="op", currency="usd"),
        ],
    ),
)
