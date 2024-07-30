from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.coinpaprika import CoinpaprikaSpotPriceSource
from telliot_feeds.sources.price.spot.uniswapV3 import UniswapV3PriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator


oeth_usd_median_feed = DataFeed(
    query=SpotPrice(asset="OETH", currency="USD"),
    source=PriceAggregator(
        asset="oeth",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="oeth", currency="usd"),
            UniswapV3PriceSource(asset="eth", currency="oeth"),
            CoinpaprikaSpotPriceSource(asset="oeth-origin-ether", currency="usd"),
        ],
    ),
)
