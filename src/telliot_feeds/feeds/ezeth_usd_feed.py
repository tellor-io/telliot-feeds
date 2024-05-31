from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.coinpaprika import CoinpaprikaSpotPriceSource
from telliot_feeds.sources.price.spot.curvefiprice import CurveFiUSDPriceSource
from telliot_feeds.sources.price.spot.uniswapV3 import UniswapV3PriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator


ezeth_usd_median_feed = DataFeed(
    query=SpotPrice(asset="EZETH", currency="USD"),
    source=PriceAggregator(
        asset="ezeth",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="ezeth", currency="usd"),
            CurveFiUSDPriceSource(asset="ezeth", currency="usd"),
            CoinpaprikaSpotPriceSource(asset="ezeth-renzo-restaked-eth", currency="usd"),
            UniswapV3PriceSource(asset="ezeth", currency="usd"),
        ],
    ),
)
