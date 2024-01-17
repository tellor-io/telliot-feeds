from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator


meth_usd_median_feed = DataFeed(
    query=SpotPrice(asset="METH", currency="USD"),
    source=PriceAggregator(
        asset="meth",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="meth", currency="usd"),
        ],
    ),
)
#https://fusionx.finance/info/v3/tokens/0xcda86a272531e8640cd7f1a92c01839911b90bb0
#eth contract address 0xd5F7838F5C461fefF7FE49ea5ebaF7728bB0ADfa
