from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.coinpaprika import CoinpaprikaSpotPriceSource
from telliot_feeds.sources.price.spot.curvefiprice import CurveFiUSDPriceSource
from telliot_feeds.sources.price.spot.uniswapV3 import UniswapV3PriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator


pufeth_usd_median_feed = DataFeed(
    query=SpotPrice(asset="pufeth", currency="usd"),
    source=PriceAggregator(
        asset="pufeth",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="pufeth", currency="usd"),
            CoinpaprikaSpotPriceSource(asset="pufeth-pufeth", currency="usd"),
            UniswapV3PriceSource(asset="pufeth", currency="usd"),
            CurveFiUSDPriceSource(asset="pufeth", currency="usd"),
        ],
    ),
)
