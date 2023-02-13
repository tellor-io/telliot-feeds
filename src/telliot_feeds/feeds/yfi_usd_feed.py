from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coinbase import CoinbaseSpotPriceSource
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.gemini import GeminiSpotPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator

yfi_usd_median_feed = DataFeed(
    query=SpotPrice(asset="YFI", currency="USD"),
    source=PriceAggregator(
        asset="yfi",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="yfi", currency="usd"),
            CoinbaseSpotPriceSource(asset="yfi", currency="usd"),
            GeminiSpotPriceSource(asset="yfi", currency="usd"),
        ],
    ),
)
