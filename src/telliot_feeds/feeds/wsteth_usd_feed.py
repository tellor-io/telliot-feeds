from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.coinpaprika import CoinpaprikaSpotPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator

wsteth_usd_median_feed = DataFeed(
    query=SpotPrice(asset="WSTETH", currency="USD"),
    source=PriceAggregator(
        asset="wsteth",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="wsteth", currency="usd"),
            CoinpaprikaSpotPriceSource(asset="wsteth-wrapped-liquid-staked-ether-20", currency="usd"),
        ],
    ),
)
