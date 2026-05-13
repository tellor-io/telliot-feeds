from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.coinpaprika import CoinpaprikaSpotPriceSource
from telliot_feeds.sources.price.spot.curvefiprice import CurveFiUSDPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator


usde_usd_median_feed = DataFeed(
    query=SpotPrice(asset="USDe", currency="USD"),
    source=PriceAggregator(
        asset="usde",
        currency="usd",
        algorithm="median",
        sources=[
            CurveFiUSDPriceSource(asset="usde", currency="usd"),
            CoinGeckoSpotPriceSource(asset="usde", currency="usd"),
            CoinpaprikaSpotPriceSource(asset="usde-ethena-usde", currency="usd"),
        ],
    ),
)
