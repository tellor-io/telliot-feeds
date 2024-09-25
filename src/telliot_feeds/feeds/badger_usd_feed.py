from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.kraken import KrakenSpotPriceSource
from telliot_feeds.sources.price.spot.okx import OKXSpotPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator

# from telliot_feeds.sources.price.spot.binance import BinanceSpotPriceSource

badger_usd_median_feed = DataFeed(
    query=SpotPrice(asset="BADGER", currency="USD"),
    source=PriceAggregator(
        asset="badger",
        currency="usd",
        algorithm="median",
        sources=[
            # BinanceSpotPriceSource(asset="badger", currency="usd"),
            CoinGeckoSpotPriceSource(asset="badger", currency="usd"),
            KrakenSpotPriceSource(asset="badger", currency="usd"),
            OKXSpotPriceSource(asset="badger", currency="usdt"),
        ],
    ),
)
