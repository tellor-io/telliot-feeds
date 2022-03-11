from telliot_core.datafeed import DataFeed
from telliot_core.queries import SpotPrice

from telliot_feed_examples.sources.price.spot.binance import BinanceSpotPriceSource
from telliot_feed_examples.sources.price.spot.bittrex import BittrexSpotPriceSource
from telliot_feed_examples.sources.price.spot.coinbase import CoinbaseSpotPriceSource
from telliot_feed_examples.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feed_examples.sources.price.spot.gemini import GeminiSpotPriceSource
from telliot_feed_examples.sources.price.spot.kraken import KrakenSpotPriceSource
from telliot_feed_examples.sources.price_aggregator import PriceAggregator

matic_usd_median_feed = DataFeed(
    query=SpotPrice(asset="MATIC", currency="USD"),
    source=PriceAggregator(
        asset="matic",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="matic", currency="usd"),
            BittrexSpotPriceSource(asset="matic", currency="usd"),
            BinanceSpotPriceSource(asset="matic", currency="usdt"),
            CoinbaseSpotPriceSource(asset="matic", currency="usd"),
            GeminiSpotPriceSource(asset="matic", currency="usd"),
            KrakenSpotPriceSource(asset="matic", currency="usd"),
        ],
    ),
)
