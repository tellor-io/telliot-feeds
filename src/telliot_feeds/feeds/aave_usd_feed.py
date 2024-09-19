from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.coinpaprika import CoinpaprikaSpotPriceSource
from telliot_feeds.sources.price.spot.kraken import KrakenSpotPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator

aave_usd_median_feed = DataFeed(
    query=SpotPrice(asset="AAVE", currency="USD"),
    source=PriceAggregator(
        asset="aave",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="aave", currency="usd"),
            KrakenSpotPriceSource(asset="aave", currency="usd"),
            CoinpaprikaSpotPriceSource(asset="aave-new", currency="usd"),
        ],
    ),
)
