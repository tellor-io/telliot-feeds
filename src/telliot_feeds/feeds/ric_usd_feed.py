from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.nomics import NomicsSpotPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator

ric_usd_median_feed = DataFeed(
    query=SpotPrice(asset="RIC", currency="USD"),
    source=PriceAggregator(
        asset="ric",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="ric", currency="usd"),
            NomicsSpotPriceSource(asset="ric", currency="usd"),
        ],
    ),
)
