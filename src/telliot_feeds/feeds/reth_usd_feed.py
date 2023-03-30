from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.coinpaprika import CoinpaprikaSpotPriceSource
from telliot_feeds.sources.price.spot.uniswapV3 import UniswapV3PriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator

reth_usd_median_feed = DataFeed(
    query=SpotPrice(asset="RETH", currency="USD"),
    source=PriceAggregator(
        asset="reth",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="reth", currency="usd"),
            CoinpaprikaSpotPriceSource(asset="reth-rocket-pool-eth", currency="usd"),
            UniswapV3PriceSource(asset="reth", currency="usd"),
        ],
    ),
)
