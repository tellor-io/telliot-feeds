from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.binance import BinanceSpotPriceSource
from telliot_feeds.sources.price.spot.coinbase import CoinbaseSpotPriceSource
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.gemini import GeminiSpotPriceSource
from telliot_feeds.sources.price.spot.kraken import KrakenSpotPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator

matic_usd_median_feed = DataFeed(
    query=SpotPrice(asset="MATIC", currency="USD"),
    source=PriceAggregator(
        asset="matic",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="matic", currency="usd"),
            BinanceSpotPriceSource(asset="matic", currency="usdt"),
            CoinbaseSpotPriceSource(asset="matic", currency="usd"),
            GeminiSpotPriceSource(asset="matic", currency="usd"),
            KrakenSpotPriceSource(asset="matic", currency="usd"),
        ],
    ),
)
