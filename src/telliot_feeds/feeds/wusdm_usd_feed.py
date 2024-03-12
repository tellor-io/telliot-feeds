from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.curvefiprice import CurveFiUSDPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator


wusdm_usd_median_feed = DataFeed(
    query=SpotPrice(asset="wUSDM", currency="USD"),
    source=PriceAggregator(
        asset="wusdm",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="wusdm", currency="usd"),
            CurveFiUSDPriceSource(asset="wusdm", currency="usd"),
        ],
    ),
)
