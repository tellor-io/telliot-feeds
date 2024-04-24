from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.curvefiprice import CurveFiUSDPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator

frxeth_usd_median_feed = DataFeed(
    query=SpotPrice(asset="FRXETH", currency="USD"),
    source=PriceAggregator(
        asset="frxeth",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="frxeth", currency="usd"),
            CurveFiUSDPriceSource(asset="frxeth", currency="usd"),
        ],
    ),
)
