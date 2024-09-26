from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.gemini import GeminiSpotPriceSource
from telliot_feeds.sources.price.spot.uniswapV3 import UniswapV3PriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator

# from telliot_feeds.sources.price.spot.binance import BinanceSpotPriceSource

dai_usd_median_feed = DataFeed(
    query=SpotPrice(asset="DAI", currency="USD"),
    source=PriceAggregator(
        asset="dai",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="dai", currency="usd"),
            # BinanceSpotPriceSource(asset="dai", currency="usdt"),
            GeminiSpotPriceSource(asset="dai", currency="usd"),
            UniswapV3PriceSource(asset="dai", currency="usd"),
        ],
    ),
)
