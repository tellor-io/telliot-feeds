from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coinpaprika import CoinpaprikaSpotPriceSource
from telliot_feeds.sources.price.spot.uniswapV3Pool import UniswapV3PoolPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator


ogv_eth_median_feed = DataFeed(
    query=SpotPrice(asset="ogv", currency="ETH"),
    source=PriceAggregator(
        asset="ogv",
        currency="eth",
        algorithm="median",
        sources=[
            CoinpaprikaSpotPriceSource(asset="ogv-origin-dollar-governance", currency="eth"),
            UniswapV3PoolPriceSource(asset="ogv", currency="eth"),
        ],
    ),
)
