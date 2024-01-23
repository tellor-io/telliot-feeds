from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.agni import agniFinancePriceSource
from telliot_feeds.sources.price.spot.coinbase import CoinbaseSpotPriceSource
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.gemini import GeminiSpotPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator

usdt_usd_median_feed = DataFeed(
    query=SpotPrice(asset="USDT", currency="USD"),
    source=PriceAggregator(
        asset="usdt",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="usdt", currency="usd"),
            CoinbaseSpotPriceSource(asset="usdt", currency="usd"),
            GeminiSpotPriceSource(asset="usdt", currency="usd"),
            agniFinancePriceSource(asset="usdt", currency="usd"),
        ],
    ),
)
