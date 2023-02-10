from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coinbase import CoinbaseSpotPriceSource
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.kraken import KrakenSpotPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator

badger_usd_median_feed = DataFeed(
    query=SpotPrice(asset="BADGER", currency="USD"),
    source=PriceAggregator(
        asset="badger",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="badger", currency="usd"),
            CoinbaseSpotPriceSource(asset="badger", currency="usd"),
            KrakenSpotPriceSource(asset="badger", currency="usd"),
        ],
    ),
)
