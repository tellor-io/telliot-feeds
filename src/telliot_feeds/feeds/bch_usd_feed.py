from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coinbase import CoinbaseSpotPriceSource
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.kraken import KrakenSpotPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator

bch_usd_median_feed = DataFeed(
    query=SpotPrice(asset="BCH", currency="USD"),
    source=PriceAggregator(
        asset="bch",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="bch", currency="usd"),
            CoinbaseSpotPriceSource(asset="bch", currency="usd"),
            KrakenSpotPriceSource(asset="bch", currency="usd"),
        ],
    ),
)
