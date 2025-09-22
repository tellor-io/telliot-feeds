from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.coinpaprika import CoinpaprikaSpotPriceSource
from telliot_feeds.sources.price.spot.uniswapV3 import UniswapV3PriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator


tbtc_usd_median_feed = DataFeed(
    query=SpotPrice(asset="SAGA", currency="USD"),
    source=PriceAggregator(
        asset="tbtc",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="tbtc", currency="usd"),
            CoinpaprikaSpotPriceSource(asset="tbtc-tbtc", currency="usd"),
            UniswapV3PriceSource(asset="tbtc", currency="usd"),
        ],
    ),
)
