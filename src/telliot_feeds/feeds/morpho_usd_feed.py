from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coinpaprika import CoinpaprikaSpotPriceSource
from telliot_feeds.sources.price.spot.kraken import KrakenSpotPriceSource
from telliot_feeds.sources.price.spot.okx import OKXSpotPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator

morpho_usd_median_feed = DataFeed(
    query=SpotPrice(asset="MORPHO", currency="USD"),
    source=PriceAggregator(
        asset="morpho",
        currency="usd",
        algorithm="median",
        sources=[
            KrakenSpotPriceSource(asset="morpho", currency="usd"),
            OKXSpotPriceSource(asset="morpho", currency="usdt"),
            CoinpaprikaSpotPriceSource(asset="morpho-morpho", currency="usd"),
        ],
    ),
)
