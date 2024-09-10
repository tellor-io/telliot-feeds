from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.coinpaprika import CoinpaprikaSpotPriceSource
from telliot_feeds.sources.price.spot.nuri import nuriSpotPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator


stone_usd_median_feed = DataFeed(
    query=SpotPrice(asset="stone", currency="usd"),
    source=PriceAggregator(
        asset="stone",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="stone", currency="usd"),
            CoinpaprikaSpotPriceSource(asset="stone-stakestone-ether", currency="usd"),
            nuriSpotPriceSource(asset="stone", currency="usd"),
        ],
    ),
)
