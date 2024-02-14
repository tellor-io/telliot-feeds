from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.uniswapV3Pool import UniswapV3PoolPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator


primeeth_eth_median_feed = DataFeed(
    query=SpotPrice(asset="PRIMEETH", currency="ETH"),
    source=PriceAggregator(
        asset="primeeth",
        currency="eth",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="primeeth", currency="eth"),
            UniswapV3PoolPriceSource(asset="primeeth", currency="eth"),
        ],
    ),
)
