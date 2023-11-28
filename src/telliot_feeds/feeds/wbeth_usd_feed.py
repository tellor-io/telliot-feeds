from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.coinpaprika import CoinpaprikaSpotPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator

wbeth_usd_median_feed = DataFeed(
    query=SpotPrice(asset="WBETH", currency="USD"),
    source=PriceAggregator(
        asset="wbeth",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="wbeth", currency="usd"),
            CoinpaprikaSpotPriceSource(asset="wbeth-wrapped-beacon-eth", currency="usd"),
        ],
    ),
)
