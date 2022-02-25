from telliot_core.datafeed import DataFeed
from telliot_core.queries import SpotPrice

from telliot_feed_examples.sources.price.spot.binance import BinancePriceSource
from telliot_feed_examples.sources.price.spot.bittrex import BittrexPriceSource
from telliot_feed_examples.sources.price.spot.coinbase import CoinbasePriceSource
from telliot_feed_examples.sources.price.spot.coingecko import CoinGeckoPriceSource
from telliot_feed_examples.sources.price.spot.gemini import GeminiPriceSource
from telliot_feed_examples.sources.price_aggregator import PriceAggregator

dai_usd_median_feed = DataFeed(
    query=SpotPrice(asset="DAI", currency="USD"),
    source=PriceAggregator(
        asset="dai",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoPriceSource(asset="dai", currency="usd"),
            CoinbasePriceSource(asset="dai", currency="usd"),
            BinancePriceSource(asset="dai", currency="usdt"),
            GeminiPriceSource(asset="dai", currency="usd"),
            BittrexPriceSource(asset="dai", currency="usd"),
        ],
    ),
)
