from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.nomics import NomicsSpotPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator

idle_usd_median_feed = DataFeed(
    query=SpotPrice(asset="IDLE", currency="USD"),
    source=PriceAggregator(
        asset="idle",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="idle", currency="usd"),
            NomicsSpotPriceSource(asset="idle", currency="usd"),
        ],
    ),
)
