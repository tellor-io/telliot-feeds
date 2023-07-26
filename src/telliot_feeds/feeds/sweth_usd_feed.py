from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.uniswapV3 import UniswapV3PriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator

sweth_usd_median_feed = DataFeed(
    query=SpotPrice(asset="SWETH", currency="USD"),
    source=PriceAggregator(
        asset="sweth",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="sweth", currency="usd"),
            UniswapV3PriceSource(asset="sweth", currency="usd"),
        ],
    ),
)
