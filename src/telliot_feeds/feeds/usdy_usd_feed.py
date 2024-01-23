from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.agni import agniFinancePriceSource
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.fusionX import fusionXPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator


usdy_usd_median_feed = DataFeed(
    query=SpotPrice(asset="USDY", currency="USD"),
    source=PriceAggregator(
        asset="usdy",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="usdy", currency="usd"),
            agniFinancePriceSource(asset="usdy", currency="usd"),
            fusionXPriceSource(asset="usdy", currency="usd"),
        ],
    ),
)
