from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.coinmarketcap import CoinMarketCapSpotPriceSource
from telliot_feeds.sources.price.spot.coinpaprika import CoinpaprikaSpotPriceSource
from telliot_feeds.sources.price.spot.curvefiprice import CurveFiUSDPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator

sfrxusd_usd_median_feed = DataFeed(
    query=SpotPrice(asset="sfrxUSD", currency="USD"),
    source=PriceAggregator(
        asset="sfrxusd",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="sfrxusd", currency="usd"),
            CurveFiUSDPriceSource(asset="sfrxusd", currency="usd"),
            CoinpaprikaSpotPriceSource(asset="sfrxusd-staked-frax-usd", currency="usd"),
            CoinMarketCapSpotPriceSource(asset="sfrxusd", currency="usd"),
        ],
    ),
)
