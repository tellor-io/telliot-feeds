from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator

# from telliot_feeds.sources.price.spot.uniswapV3 import UniswapV3PriceSource

diva_usd_median_feed = DataFeed(
    query=SpotPrice(asset="DIVA", currency="USD"),
    source=PriceAggregator(
        asset="diva",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="diva", currency="usd"),
            # UniswapV3PriceSource(asset="diva", currency="usd"),
        ],
    ),
)
