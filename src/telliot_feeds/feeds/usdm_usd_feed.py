from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.coinpaprika import CoinpaprikaSpotPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator


usdm_usd_median_feed = DataFeed(
    query=SpotPrice(asset="USDM", currency="USD"),
    source=PriceAggregator(
        asset="usdm",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="usdm", currency="usd"),
            CoinpaprikaSpotPriceSource(asset="usdm-mountain-protocol-usd", currency="usd"),
        ],
    ),
)
