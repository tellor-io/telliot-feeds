from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.coinpaprika import CoinpaprikaSpotPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator


fbtc_usd_median_feed = DataFeed(
    query=SpotPrice(asset="FBTC", currency="USD"),
    source=PriceAggregator(
        asset="fbtc",
        currency="usd",
        algorithm="median",
        sources=[
            CoinpaprikaSpotPriceSource(asset="fbtc-ignition-fbtc", currency="usd"),
            CoinGeckoSpotPriceSource(asset="fbtc", currency="usd"),
        ],
    ),
)
