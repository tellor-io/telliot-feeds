from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.uniswapV3 import UniswapV3PriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator
from telliot_feeds.sources.sweth_source import swETHSpotPriceSource


sweth_usd_median_feed = DataFeed(
    query=SpotPrice(asset="SWETH", currency="USD"),
    source=PriceAggregator(
        asset="sweth",
        currency="usd",
        algorithm="median",
        sources=[
            swETHSpotPriceSource(asset="sweth", currency="usd"),
            CoinGeckoSpotPriceSource(asset="sweth", currency="usd"),
            UniswapV3PriceSource(asset="sweth", currency="usd"),
        ],
    ),
)
