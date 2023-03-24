from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.coinpaprika import CoinpaprikaSpotPriceSource
from telliot_feeds.sources.price.spot.curvefi import CurveFinanceSpotPriceSource
from telliot_feeds.sources.price.spot.uniswapV3 import UniswapV3PriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator

steth_usd_median_feed = DataFeed(
    query=SpotPrice(asset="STETH", currency="USD"),
    source=PriceAggregator(
        asset="steth",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="steth", currency="usd"),
            UniswapV3PriceSource(asset="steth", currency="usd"),
            CoinpaprikaSpotPriceSource(asset="steth-lido-staked-ether", currency="usd"),
            CurveFinanceSpotPriceSource(asset="steth", currency="usd"),
        ],
    ),
)
