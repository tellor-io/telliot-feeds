from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.coinpaprika import CoinpaprikaSpotPriceSource
from telliot_feeds.sources.price.spot.uniswapV3 import UniswapV3PriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator

cbeth_usd_median_feed = DataFeed(
    query=SpotPrice(asset="CBETH", currency="USD"),
    source=PriceAggregator(
        asset="cbeth",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="cbeth", currency="usd"),
            UniswapV3PriceSource(asset="cbeth", currency="usd"),
            CoinpaprikaSpotPriceSource(asset="cbeth-coinbase-wrapped-staked-eth", currency="usd"),
        ],
    ),
)
