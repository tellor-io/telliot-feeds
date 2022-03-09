from telliot_core.datafeed import DataFeed
from telliot_core.queries import SpotPrice

from telliot_feed_examples.sources.price.spot.binance import BinanceSpotPriceSource
from telliot_feed_examples.sources.price.spot.bittrex import BittrexSpotPriceSource
from telliot_feed_examples.sources.price.spot.coinbase import CoinbaseSpotPriceSource
from telliot_feed_examples.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feed_examples.sources.price.spot.gemini import GeminiSpotPriceSource
from telliot_feed_examples.sources.price.spot.kraken import KrakenSpotPriceSource
from telliot_feed_examples.sources.price_aggregator import PriceAggregator

sushi_usd_median_feed = DataFeed(
    query=SpotPrice(asset="SUSHI", currency="USD"),
    source=PriceAggregator(
        asset="sushi",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="sushi", currency="usd"),
            BittrexSpotPriceSource(asset="sushi", currency="usd"),
            BinanceSpotPriceSource(asset="sushi", currency="usdt"),
            CoinbaseSpotPriceSource(asset="sushi", currency="usd"),
            GeminiSpotPriceSource(asset="sushi", currency="usd"),
            KrakenSpotPriceSource(asset="sushi", currency="usd"),
        ],
    ),
)
