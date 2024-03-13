from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.coinpaprika import CoinpaprikaSpotPriceSource
from telliot_feeds.sources.price.spot.curvefiprice import CurveFiUSDPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator

sdai_usd_median_feed = DataFeed(
    query=SpotPrice(asset="SDAI", currency="USD"),
    source=PriceAggregator(
        asset="sdai",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="sdai", currency="usd"),
            CoinpaprikaSpotPriceSource(asset="sdai-savings-dai", currency="usd"),
            CurveFiUSDPriceSource(asset="sdai", currency="usd"),
        ],
    ),
)
