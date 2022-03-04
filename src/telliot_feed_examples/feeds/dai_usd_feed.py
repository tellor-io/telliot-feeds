from telliot_core.datafeed import DataFeed
from telliot_core.queries import SpotPrice

from telliot_feed_examples.sources.price.spot.binance import BinanceSpotPriceSource
from telliot_feed_examples.sources.price.spot.bittrex import BittrexSpotPriceSource
from telliot_feed_examples.sources.price.spot.coinbase import CoinbaseSpotPriceSource
from telliot_feed_examples.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feed_examples.sources.price.spot.gemini import GeminiSpotPriceSource
from telliot_feed_examples.sources.price_aggregator import PriceAggregator

dai_usd_median_feed = DataFeed(
    query=SpotPrice(asset="DAI", currency="USD"),
    source=PriceAggregator(
        asset="dai",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="dai", currency="usd"),
            CoinbaseSpotPriceSource(asset="dai", currency="usd"),
            BinanceSpotPriceSource(asset="dai", currency="usdt"),
            GeminiSpotPriceSource(asset="dai", currency="usd"),
            BittrexSpotPriceSource(asset="dai", currency="usd"),
        ],
    ),
)
