from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coinbase import CoinbaseSpotPriceSource
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.kraken import KrakenSpotPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator

link_usd_median_feed = DataFeed(
    query=SpotPrice(asset="LINK", currency="USD"),
    source=PriceAggregator(
        asset="link",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="link", currency="usd"),
            CoinbaseSpotPriceSource(asset="link", currency="usd"),
            KrakenSpotPriceSource(asset="link", currency="usd"),
        ],
    ),
)
