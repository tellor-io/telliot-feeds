from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.binance import BinanceSpotPriceSource
from telliot_feeds.sources.price.spot.coinbase import CoinbaseSpotPriceSource
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.gemini import GeminiSpotPriceSource
from telliot_feeds.sources.price.spot.kraken import KrakenSpotPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator

mkr_usd_median_feed = DataFeed(
    query=SpotPrice(asset="MKR", currency="USD"),
    source=PriceAggregator(
        asset="mkr",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="mkr", currency="usd"),
            BinanceSpotPriceSource(asset="mkr", currency="usdt"),
            CoinbaseSpotPriceSource(asset="mkr", currency="usd"),
            GeminiSpotPriceSource(asset="mkr", currency="usd"),
            KrakenSpotPriceSource(asset="mkr", currency="usd"),
        ],
    ),
)
