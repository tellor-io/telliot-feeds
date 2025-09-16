from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.coinmarketcap import CoinMarketCapSpotPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator

# from telliot_feeds.sources.price.spot.binance import BinanceSpotPriceSource

statom_usd_median_feed = DataFeed(
    query=SpotPrice(asset="stATOM", currency="USD"),
    source=PriceAggregator(
        asset="statom",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="statom", currency="usd"),
            CoinMarketCapSpotPriceSource(asset="statom", currency="usd"),
        ],
    ),
)
