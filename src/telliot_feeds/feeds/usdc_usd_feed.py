from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.binance import BinanceSpotPriceSource
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.gemini import GeminiSpotPriceSource
from telliot_feeds.sources.price.spot.kraken import KrakenSpotPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator

usdc_usd_median_feed = DataFeed(
    query=SpotPrice(asset="USDC", currency="USD"),
    source=PriceAggregator(
        asset="usdc",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="usdc", currency="usd"),
            BinanceSpotPriceSource(asset="usdc", currency="usdt"),
            GeminiSpotPriceSource(asset="usdc", currency="usd"),
            KrakenSpotPriceSource(asset="usdc", currency="usd"),
        ],
    ),
)
