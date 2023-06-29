from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.uniswapV3 import UniswapV3PriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator

# from telliot_feeds.sources.price.spot.curvefi import CurveFinanceSpotPriceSource

ousd_usd_median_feed = DataFeed(
    query=SpotPrice(asset="OUSD", currency="USD"),
    source=PriceAggregator(
        asset="ousd",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="ousd", currency="usd"),
            UniswapV3PriceSource(asset="ousd", currency="usd"),
            # CurveFinanceSpotPriceSource(asset="ousd", currency="usd"),
        ],
    ),
)
