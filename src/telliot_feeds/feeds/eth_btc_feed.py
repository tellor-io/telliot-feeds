from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.gemini import GeminiSpotPriceSource
from telliot_feeds.sources.price.spot.okx import OKXSpotPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator

# from telliot_feeds.sources.price.spot.binance import BinanceSpotPriceSource

eth_btc_median_feed = DataFeed(
    query=SpotPrice(asset="ETH", currency="BTC"),
    source=PriceAggregator(
        asset="eth",
        currency="btc",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="eth", currency="btc"),
            # BinanceSpotPriceSource(asset="eth", currency="btc"),
            GeminiSpotPriceSource(asset="eth", currency="btc"),
            OKXSpotPriceSource(asset="eth", currency="btc"),
        ],
    ),
)
