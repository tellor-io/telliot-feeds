from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.coinmarketcap import CoinMarketCapSpotPriceSource
from telliot_feeds.sources.price.spot.kraken import KrakenSpotPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator


saga_usd_median_feed = DataFeed(
    query=SpotPrice(asset="SAGA", currency="USD"),
    source=PriceAggregator(
        asset="saga",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="saga", currency="usd"),
            KrakenSpotPriceSource(asset="saga", currency="usd"),
            CoinMarketCapSpotPriceSource(asset="saga", currency="usd"),
        ],
    ),
)
