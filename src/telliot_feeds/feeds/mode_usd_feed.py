from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.coinpaprika import CoinpaprikaSpotPriceSource
from telliot_feeds.sources.price.spot.kimexchange import kimexchangePriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator

mode_usd_median_feed = DataFeed(
    query=SpotPrice(asset="MODE", currency="USD"),
    source=PriceAggregator(
        asset="mode",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="mode", currency="usd"),
            CoinpaprikaSpotPriceSource(asset="mode-mode", currency="usd"),
            kimexchangePriceSource(asset="mode", currency="usd"),
        ],
    ),
)
