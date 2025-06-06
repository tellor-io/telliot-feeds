from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.osgno_source import osGNOSpotPriceSource
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator

osgno_usd_median_feed = DataFeed(
    query=SpotPrice(asset="OSGNO", currency="USD"),
    source=PriceAggregator(
        asset="osgno",
        currency="usd",
        algorithm="median",
        sources=[
            osGNOSpotPriceSource(asset="osgno", currency="usd"),
            CoinGeckoSpotPriceSource(asset="osgno", currency="usd"),
        ],
    ),
)
