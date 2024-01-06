from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.custom_price import CustomPrice
from telliot_feeds.sources.custom_price_aggregator import CustomPriceAggregator
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoBRC20SpotPriceSource

ordi_usd_median_feed = DataFeed(
    query=CustomPrice(identifier="brc20", asset="ordi", currency="usd", unit=""),
    source=CustomPriceAggregator(
        identifier="brc20",
        asset="ordi",
        currency="usd",
        unit="",
        algorithm="median",
        sources=[
            CoinGeckoBRC20SpotPriceSource(identifier="brc20", asset="ordi", currency="usd", unit=""),
        ],
    ),
)
