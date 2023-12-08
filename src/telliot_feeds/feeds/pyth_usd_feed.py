from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.kraken import KrakenSpotPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator

pyth_usd_median_feed = DataFeed(
    query=SpotPrice(asset="PYTH", currency="USD"),
    source=PriceAggregator(
        asset="pyth",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="pyth", currency="usd"),
            KrakenSpotPriceSource(asset="pyth", currency="usd"),
        ],
    ),
)
