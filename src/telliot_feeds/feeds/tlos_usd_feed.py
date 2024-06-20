from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.bitfinex import BitfinexSpotPriceSource
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.coinpaprika import CoinpaprikaSpotPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator

tlos_usd_median_feed = DataFeed(
    query=SpotPrice(asset="TLOS", currency="USD"),
    source=PriceAggregator(
        asset="tlos",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="tlos", currency="usd"),
            BitfinexSpotPriceSource(asset="TLOS", currency="USD"),
            CoinpaprikaSpotPriceSource(asset="tlos-telos", currency="usd"),
        ],
    ),
)
