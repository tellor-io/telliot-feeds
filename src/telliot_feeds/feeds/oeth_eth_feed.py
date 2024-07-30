from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.coinpaprika import CoinpaprikaSpotPriceSource
from telliot_feeds.sources.price.spot.uniswapV3Pool import UniswapV3PoolPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator


oeth_eth_median_feed = DataFeed(
    query=SpotPrice(asset="OETH", currency="ETH"),
    source=PriceAggregator(
        asset="oeth",
        currency="eth",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="oeth", currency="eth"),
            UniswapV3PoolPriceSource(asset="oeth", currency="eth"),
            CoinpaprikaSpotPriceSource(asset="oeth-origin-ether", currency="eth"),
        ],
    ),
)
