from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.coinpaprika import CoinpaprikaSpotPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator

tara_usd_median_feed = DataFeed(
    query=SpotPrice(asset="TARA", currency="USD"),
    source=PriceAggregator(
        asset="tara",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="tara", currency="usd"),
            CoinpaprikaSpotPriceSource(asset="tara-taraxa", currency="usd"),
        ],
    ),
)
