from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coinbase import CoinbaseSpotPriceSource
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.gemini import GeminiSpotPriceSource
from telliot_feeds.sources.price.spot.kraken import KrakenSpotPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator

eth_usd_median_feed = DataFeed(
    query=SpotPrice(asset="ETH", currency="USD"),
    source=PriceAggregator(
        asset="eth",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="eth", currency="usd"),
            CoinbaseSpotPriceSource(asset="eth", currency="usd"),
            GeminiSpotPriceSource(asset="eth", currency="usd"),
            KrakenSpotPriceSource(asset="eth", currency="usd"),
        ],
    ),
)
