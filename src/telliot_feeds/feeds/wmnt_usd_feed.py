from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.agni import agniFinancePriceSource
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.fusionX import fusionXPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator


wmnt_usd_median_feed = DataFeed(
    query=SpotPrice(asset="WMNT", currency="USD"),
    source=PriceAggregator(
        asset="wmnt",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="wmnt", currency="usd"),
            agniFinancePriceSource(asset="wmnt", currency="usd"),
            fusionXPriceSource(asset="wmnt", currency="usd"),
        ],
    ),
)
