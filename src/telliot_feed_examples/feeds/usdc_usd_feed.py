from telliot_core.datafeed import DataFeed
from telliot_core.queries import SpotPrice
from telliot_core.sources.price.spot.binance import BinanceSpotPriceSource
from telliot_core.sources.price.spot.bittrex import BittrexSpotPriceSource
from telliot_core.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_core.sources.price.spot.gemini import GeminiSpotPriceSource
from telliot_core.sources.price.spot.kraken import KrakenSpotPriceSource
from telliot_core.sources.price_aggregator import PriceAggregator

usdc_usd_median_feed = DataFeed(
    query=SpotPrice(asset="USDC", currency="USD"),
    source=PriceAggregator(
        asset="usdc",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="usdc", currency="usd"),
            BittrexSpotPriceSource(asset="usdc", currency="usd"),
            BinanceSpotPriceSource(asset="usdc", currency="usdt"),
            GeminiSpotPriceSource(asset="usdc", currency="usd"),
            KrakenSpotPriceSource(asset="usdc", currency="usd"),
        ],
    ),
)
