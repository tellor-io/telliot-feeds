from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.lfj_source import LFJPriceSource
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.coinpaprika import CoinpaprikaSpotPriceSource
from telliot_feeds.sources.price.spot.curvefiprice import CurveFiUSDPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator

solvbtc_usd_median_feed = DataFeed(
    query=SpotPrice(asset="SOLVBTC", currency="USD"),
    source=PriceAggregator(
        asset="solvbtc",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="solvbtc", currency="usd"),
            CoinpaprikaSpotPriceSource(asset="solvbtc-solv-protocol-solvbtc", currency="usd"),
            CurveFiUSDPriceSource(asset="solvbtc", currency="usd"),
            LFJPriceSource(asset="solvbtc", currency="usd"),
        ],
    ),
)
