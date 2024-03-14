from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.coinpaprika import CoinpaprikaSpotPriceSource
from telliot_feeds.sources.price.spot.curvefiprice import CurveFiUSDPriceSource
from telliot_feeds.sources.price.spot.uniswapV3 import UniswapV3PriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator


frax_usd_median_feed = DataFeed(
    query=SpotPrice(asset="FRAX", currency="USD"),
    source=PriceAggregator(
        asset="frax",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="frax", currency="usd"),
            CurveFiUSDPriceSource(asset="frax", currency="usd"),
            CoinpaprikaSpotPriceSource(asset="frax-frax", currency="usd"),
            UniswapV3PriceSource(asset="frax", currency="usd"),
        ],
    ),
)
