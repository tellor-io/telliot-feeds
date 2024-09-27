from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.coinpaprika import CoinpaprikaSpotPriceSource
from telliot_feeds.sources.price.spot.kraken import KrakenSpotPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator

avax_usd_median_feed = DataFeed(
    query=SpotPrice(asset="AVAX", currency="USD"),
    source=PriceAggregator(
        asset="avax",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="avax", currency="usd"),
            KrakenSpotPriceSource(asset="avax", currency="usd"),
            CoinpaprikaSpotPriceSource(asset="avax-avalanche", currency="usd"),
        ],
    ),
)
