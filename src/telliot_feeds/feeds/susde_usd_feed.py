from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.coinmarketcap import CoinMarketCapSpotPriceSource
from telliot_feeds.sources.price.spot.coinpaprika import CoinpaprikaSpotPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator


susde_usd_median_feed = DataFeed(
    query=SpotPrice(asset="sUSDe", currency="USD"),
    source=PriceAggregator(
        asset="susde",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="susde", currency="usd"),
            CoinMarketCapSpotPriceSource(asset="susde", currency="usd"),
            CoinpaprikaSpotPriceSource(asset="susde-ethena-staked-usde", currency="usd"),
        ],
    ),
)
