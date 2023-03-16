from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator

steth_btc_median_feed = DataFeed(
    query=SpotPrice(asset="STETH", currency="BTC"),
    source=PriceAggregator(
        asset="steth",
        currency="btc",
        algorithm="median",
        sources=[CoinGeckoSpotPriceSource(asset="steth", currency="btc")],
    ),
)
