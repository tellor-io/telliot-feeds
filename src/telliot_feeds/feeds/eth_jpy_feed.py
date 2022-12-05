"""Datafeed for current price of ETH in JPY."""
from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.bitfinex import BitfinexSpotPriceSource
from telliot_feeds.sources.price.spot.bitflyer import BitflyerSpotPriceSource
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator

eth_jpy_median_feed = DataFeed(
    query=SpotPrice(asset="ETH", currency="JPY"),
    source=PriceAggregator(
        asset="eth",
        currency="jpy",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="eth", currency="jpy"),
            BitflyerSpotPriceSource(asset="eth", currency="jpy"),
            BitfinexSpotPriceSource(asset="eth", currency="jpy"),
        ],
    ),
)
