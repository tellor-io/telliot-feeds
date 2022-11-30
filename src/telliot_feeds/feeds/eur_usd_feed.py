"""
EUR/USD SpotPrice DataFeed
"""
from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.currency.coinbase import CoinbaseCurrencyPriceSource
from telliot_feeds.sources.price.currency.openexchangerate import OpenExchangeRateCurrencyPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator

eur_usd_median_feed = DataFeed(
    query=SpotPrice(asset="EUR", currency="USD"),
    source=PriceAggregator(
        asset="eur",
        currency="usd",
        algorithm="median",
        sources=[
            CoinbaseCurrencyPriceSource(asset="eur", currency="usd"),
            OpenExchangeRateCurrencyPriceSource(asset="eur", currency="usd"),
        ],
    ),
)
