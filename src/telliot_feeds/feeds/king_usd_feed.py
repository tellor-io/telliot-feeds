from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.uniswapV3 import UniswapV3PriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator


king_usd_median_feed = DataFeed(
    query=SpotPrice(asset="KING", currency="USD"),
    source=PriceAggregator(
        asset="king",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="king", currency="usd"),
            UniswapV3PriceSource(asset="king", currency="usd"),
        ],
    ),
)
