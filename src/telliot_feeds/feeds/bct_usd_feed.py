from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.coinmarketcap import (
    CoinMarketCapSpotPriceSource,
)
from telliot_feeds.sources.price.spot.nomics import NomicsSpotPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator


bct_usd_median_feed = DataFeed(
    query=SpotPrice(asset="BCT", currency="USD"),
    source=PriceAggregator(
        asset="bct",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="bct", currency="usd"),
            NomicsSpotPriceSource(asset="bct", currency="usd"),
            CoinMarketCapSpotPriceSource(asset="bct", currency="usd"),
        ],
    ),
)
