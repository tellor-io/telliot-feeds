from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.kraken import KrakenSpotPriceSource
from telliot_feeds.sources.price.spot.okx import OKXSpotPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator

# from telliot_feeds.sources.price.spot.binance import BinanceSpotPriceSource

crv_usd_median_feed = DataFeed(
    query=SpotPrice(asset="CRV", currency="USD"),
    source=PriceAggregator(
        asset="crv",
        currency="usd",
        algorithm="median",
        sources=[
            # BinanceSpotPriceSource(asset="crv", currency="usd"),
            CoinGeckoSpotPriceSource(asset="crv", currency="usd"),
            KrakenSpotPriceSource(asset="crv", currency="usd"),
            OKXSpotPriceSource(asset="crv", currency="usdt"),
        ],
    ),
)
