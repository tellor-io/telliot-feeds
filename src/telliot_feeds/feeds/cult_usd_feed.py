from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.uniswapV3 import UniswapV3PriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator

cult_usd_median_feed = DataFeed(
    query=SpotPrice(asset="CULT", currency="USD"),
    source=PriceAggregator(
        asset="cult",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="cult", currency="usd"),
            UniswapV3PriceSource(asset="cult", currency="usd"),
        ],
    ),
)
