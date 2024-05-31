from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.coinpaprika import CoinpaprikaSpotPriceSource
from telliot_feeds.sources.price.spot.curvefiprice import CurveFiUSDPriceSource
from telliot_feeds.sources.price.spot.uniswapV3 import UniswapV3PriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator


weeth_usd_median_feed = DataFeed(
    query=SpotPrice(asset="WEETH", currency="USD"),
    source=PriceAggregator(
        asset="weeth",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="weeth", currency="usd"),
            CurveFiUSDPriceSource(asset="weeth", currency="usd"),
            CoinpaprikaSpotPriceSource(asset="weeth-wrapped-eeth", currency="usd"),
            UniswapV3PriceSource(asset="weeth", currency="usd"),
        ],
    ),
)
