"""Datafeed for current price of TRB in USD."""
from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coinbase import CoinbaseSpotPriceSource
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.coinpaprika import CoinpaprikaSpotPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator

trb_usd_median_feed = DataFeed(
    query=SpotPrice(asset="trb", currency="usd"),
    source=PriceAggregator(
        asset="trb",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="trb", currency="usd"),
            CoinbaseSpotPriceSource(asset="trb", currency="usd"),
            CoinpaprikaSpotPriceSource(asset="trb-tellor", currency="usd"),
        ],
    ),
)
