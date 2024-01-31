from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.binance import BinanceSpotPriceSource
from telliot_feeds.sources.price.spot.coinbase import CoinbaseSpotPriceSource
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.gemini import GeminiSpotPriceSource
from telliot_feeds.sources.price.spot.kraken import KrakenSpotPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator

sushi_usd_median_feed = DataFeed(
    query=SpotPrice(asset="SUSHI", currency="USD"),
    source=PriceAggregator(
        asset="sushi",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="sushi", currency="usd"),
            BinanceSpotPriceSource(asset="sushi", currency="usdt"),
            CoinbaseSpotPriceSource(asset="sushi", currency="usd"),
            GeminiSpotPriceSource(asset="sushi", currency="usd"),
            KrakenSpotPriceSource(asset="sushi", currency="usd"),
        ],
    ),
)
