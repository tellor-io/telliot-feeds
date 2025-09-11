from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.cryptodotcom import CryptodotcomSpotPriceSource
from telliot_feeds.sources.price.spot.kraken import KrakenSpotPriceSource
from telliot_feeds.sources.price.spot.okx import OKXSpotPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator

# from telliot_feeds.sources.price.spot.binance import BinanceSpotPriceSource

atom_usd_median_feed = DataFeed(
    query=SpotPrice(asset="ATOM", currency="USD"),
    source=PriceAggregator(
        asset="atom",
        currency="usd",
        algorithm="median",
        sources=[
            KrakenSpotPriceSource(asset="atom", currency="usd"),
            CryptodotcomSpotPriceSource(asset="atom", currency="usd"),
            OKXSpotPriceSource(asset="atom", currency="usdt"),
        ],
    ),
)
