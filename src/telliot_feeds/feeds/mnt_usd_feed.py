from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.coinpaprika import CoinpaprikaSpotPriceSource
from telliot_feeds.sources.price.spot.uniswapV3 import UniswapV3PriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator


mnt_usd_median_feed = DataFeed(
    query=SpotPrice(asset="MNT", currency="USD"),
    source=PriceAggregator(
        asset="mnt",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="mnt", currency="usd"),
            UniswapV3PriceSource(asset="mnt", currency="usd"),
            CoinpaprikaSpotPriceSource(asset="mnt-mantle", currency="usd"),
        ],
    ),
)
