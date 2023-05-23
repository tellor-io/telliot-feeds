from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.coinpaprika import CoinpaprikaSpotPriceSource
from telliot_feeds.sources.price.spot.uniswapV3 import UniswapV3PriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator

pepe_usd_median_feed = DataFeed(
    query=SpotPrice(asset="PEPE", currency="USD"),
    source=PriceAggregator(
        asset="pepe",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="pepe", currency="usd"),
            CoinpaprikaSpotPriceSource(asset="pepe-pepe", currency="usd"),
            UniswapV3PriceSource(asset="pepe", currency="usd"),
        ],
    ),
)
