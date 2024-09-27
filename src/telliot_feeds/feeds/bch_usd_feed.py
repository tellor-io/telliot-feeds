from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.kraken import KrakenSpotPriceSource
from telliot_feeds.sources.price.spot.okx import OKXSpotPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator

# from telliot_feeds.sources.price.spot.binance import BinanceSpotPriceSource

bch_usd_median_feed = DataFeed(
    query=SpotPrice(asset="BCH", currency="USD"),
    source=PriceAggregator(
        asset="bch",
        currency="usd",
        algorithm="median",
        sources=[
            # BinanceSpotPriceSource(asset="bch", currency="usd"),
            CoinGeckoSpotPriceSource(asset="bch", currency="usd"),
            KrakenSpotPriceSource(asset="bch", currency="usd"),
            OKXSpotPriceSource(asset="bch", currency="usdt"),
        ],
    ),
)
