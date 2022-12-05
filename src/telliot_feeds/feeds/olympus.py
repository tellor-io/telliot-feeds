from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator

ohm_eth_median_feed = DataFeed(
    query=SpotPrice(asset="OHM", currency="ETH"),
    source=PriceAggregator(
        asset="ohm",
        currency="eth",
        algorithm="median",
        sources=[CoinGeckoSpotPriceSource(asset="ohm", currency="eth")],
    ),
)
