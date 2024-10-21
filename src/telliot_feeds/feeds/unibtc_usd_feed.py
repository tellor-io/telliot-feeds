from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.coinpaprika import CoinpaprikaSpotPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator

unibtc_usd_median_feed = DataFeed(
    query=SpotPrice(asset="UNIBTC", currency="USD"),
    source=PriceAggregator(
        asset="unibtc",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="unibtc", currency="usd"),
            CoinpaprikaSpotPriceSource(asset="unibtc-universal-btc", currency="usd"),
        ],
    ),
)
