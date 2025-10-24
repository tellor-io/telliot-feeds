from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.coinpaprika import CoinpaprikaSpotPriceSource
from telliot_feeds.sources.price.spot.curvefiprice import CurveFiUSDPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator


frxusd_usd_median_feed = DataFeed(
    query=SpotPrice(asset="FRXUSD", currency="USD"),
    source=PriceAggregator(
        asset="frxusd",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="frxusd", currency="usd"),
            CurveFiUSDPriceSource(asset="frxusd", currency="usd"),
            CoinpaprikaSpotPriceSource(asset="frxusd-frax-usd", currency="usd"),
        ],
    ),
)
