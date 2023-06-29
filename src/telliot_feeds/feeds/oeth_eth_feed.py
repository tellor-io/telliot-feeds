from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator

# from telliot_feeds.sources.price.spot.curvefi import CurveFinanceSpotPriceSource
# from telliot_feeds.sources.price.spot.uniswapV3 import UniswapV3PriceSource

oeth_eth_median_feed = DataFeed(
    query=SpotPrice(asset="OETH", currency="ETH"),
    source=PriceAggregator(
        asset="oeth",
        currency="eth",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="oeth", currency="eth"),
            # UniswapV3PriceSource(asset="oeth", currency="eth"),
            # CurveFinanceSpotPriceSource(asset="oeth", currency="eth"),
        ],
    ),
)
