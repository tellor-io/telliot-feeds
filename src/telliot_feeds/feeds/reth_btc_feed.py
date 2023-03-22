from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.coinpaprika import CoinpaprikaSpotPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator

reth_btc_median_feed = DataFeed(
    query=SpotPrice(asset="RETH", currency="BTC"),
    source=PriceAggregator(
        asset="reth",
        currency="btc",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="reth", currency="btc"),
            CoinpaprikaSpotPriceSource(asset="reth-rocket-pool-eth", currency="btc"),
        ],
    ),
)
