from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.gemini import GeminiSpotPriceSource
from telliot_feeds.sources.price.spot.kraken import KrakenSpotPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator

eul_usd_median_feed = DataFeed(
    query=SpotPrice(asset="EUL", currency="USD"),
    source=PriceAggregator(
        asset="eul",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="eul", currency="usd"),
            GeminiSpotPriceSource(asset="eul", currency="usd"),
            KrakenSpotPriceSource(asset="eul", currency="usd"),
        ],
    ),
)
