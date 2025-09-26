from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator
from telliot_feeds.sources.susn_contract_source import sUSNSpotPriceSource

susn_usd_median_feed = DataFeed(
    query=SpotPrice(asset="sUSN", currency="USD"),
    source=PriceAggregator(
        asset="susn",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="susn", currency="usd"),
            sUSNSpotPriceSource(asset="susn", currency="usd"),
        ],
    ),
)
