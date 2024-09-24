from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator


superoethb_eth_median_feed = DataFeed(
    query=SpotPrice(asset="SUPEROETHB", currency="ETH"),
    source=PriceAggregator(
        asset="superoethb",
        currency="eth",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="superoethb", currency="eth"),
        ],
    ),
)
