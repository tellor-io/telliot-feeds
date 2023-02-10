from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coinbase import CoinbaseSpotPriceSource
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.kraken import KrakenSpotPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator

crv_usd_median_feed = DataFeed(
    query=SpotPrice(asset="CRV", currency="USD"),
    source=PriceAggregator(
        asset="crv",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="crv", currency="usd"),
            CoinbaseSpotPriceSource(asset="crv", currency="usd"),
            KrakenSpotPriceSource(asset="crv", currency="usd"),
        ],
    ),
)
