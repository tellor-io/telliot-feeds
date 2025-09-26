from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.coinpaprika import CoinpaprikaSpotPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator

usn_usd_median_feed = DataFeed(
    query=SpotPrice(asset="USN", currency="USD"),
    source=PriceAggregator(
        asset="usn",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="usn", currency="usd"),
            CoinpaprikaSpotPriceSource(asset="usn1-noon-usn", currency="usd"),
        ],
    ),
)
