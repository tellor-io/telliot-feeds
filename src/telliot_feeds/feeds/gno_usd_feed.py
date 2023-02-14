from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coinbase import CoinbaseSpotPriceSource
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.kraken import KrakenSpotPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator

gno_usd_median_feed = DataFeed(
    query=SpotPrice(asset="GNO", currency="USD"),
    source=PriceAggregator(
        asset="gno",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="gno", currency="usd"),
            CoinbaseSpotPriceSource(asset="gno", currency="usd"),
            KrakenSpotPriceSource(asset="gno", currency="usd"),
        ],
    ),
)
