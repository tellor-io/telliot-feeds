from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.coinpaprika import CoinpaprikaSpotPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator

xdai_usd_median_feed = DataFeed(
    query=SpotPrice(asset="XDAI", currency="USD"),
    source=PriceAggregator(
        asset="xdai",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="xdai", currency="usd"),
            CoinpaprikaSpotPriceSource(asset="xdai-xdai", currency="usd"),
        ],
    ),
)
