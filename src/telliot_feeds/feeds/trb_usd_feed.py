"""Datafeed for current price of TRB in USD."""
from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.coinpaprika import CoinpaprikaSpotPriceSource
from telliot_feeds.sources.price.spot.cryptodotcom import CryptodotcomSpotPriceSource
from telliot_feeds.sources.price.spot.okx import OKXSpotPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator

# from telliot_feeds.sources.price.spot.binance import BinanceSpotPriceSource

trb_usd_median_feed = DataFeed(
    query=SpotPrice(asset="trb", currency="usd"),
    source=PriceAggregator(
        asset="trb",
        currency="usd",
        algorithm="median",
        sources=[
            # BinanceSpotPriceSource(asset="trb", currency="usd"),
            CoinGeckoSpotPriceSource(asset="trb", currency="usd"),
            CoinpaprikaSpotPriceSource(asset="trb-tellor", currency="usd"),
            CryptodotcomSpotPriceSource(asset="trb", currency="usd"),
            OKXSpotPriceSource(asset="trb", currency="usdt"),
        ],
    ),
)
