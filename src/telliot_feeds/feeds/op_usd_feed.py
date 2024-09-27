from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.coinpaprika import CoinpaprikaSpotPriceSource
from telliot_feeds.sources.price.spot.okx import OKXSpotPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator

op_usd_median_feed = DataFeed(
    query=SpotPrice(asset="OP", currency="USD"),
    source=PriceAggregator(
        asset="op",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="op", currency="usd"),
            CoinpaprikaSpotPriceSource(asset="op-optimism", currency="usd"),
            OKXSpotPriceSource(asset="op", currency="usdt"),
        ],
    ),
)
