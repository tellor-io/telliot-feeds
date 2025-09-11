from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.coinmarketcap import CoinMarketCapSpotPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator


usdn_usd_median_feed = DataFeed(
    query=SpotPrice(asset="USDN", currency="USD"),
    source=PriceAggregator(
        asset="usdn",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="usdn", currency="usd"),
            CoinMarketCapSpotPriceSource(asset="usdn", currency="usd"),
        ],
    ),
)
