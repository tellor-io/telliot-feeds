from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.uniswapV3 import UniswapV3PriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator

steth_usd_median_feed = DataFeed(
    query=SpotPrice(asset="STETH", currency="USD"),
    source=PriceAggregator(
        asset="steth",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="steth", currency="usd"),
            UniswapV3PriceSource(asset="steth", currency="usd"),
        ],
    ),
)
