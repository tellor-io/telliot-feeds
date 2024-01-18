from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.coinpaprika import CoinpaprikaSpotPriceSource
from telliot_feeds.sources.price.spot.kraken import KrakenSpotPriceSource
from telliot_feeds.sources.price.spot.uniswapV3 import UniswapV3PriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator

wbtc_usd_median_feed = DataFeed(
    query=SpotPrice(asset="WBTC", currency="USD"),
    source=PriceAggregator(
        asset="wbtc",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="wbtc", currency="usd"),
            CoinpaprikaSpotPriceSource(asset="wbtc-wrapped-bitcoin", currency="eth"),
            KrakenSpotPriceSource(asset="wbtc", currency="usd"),
            UniswapV3PriceSource(asset="wbtc", currency="usd"),
        ],
    ),
)
