import asyncio

from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.coinpaprika import CoinpaprikaSpotPriceSource
from telliot_feeds.sources.price.spot.uniswapV3 import UniswapV3PriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator


rai_usd_median_feed = DataFeed(
    query=SpotPrice(asset="RAI", currency="USD"),
    source=PriceAggregator(
        asset="rai",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="rai", currency="usd"),
            CoinpaprikaSpotPriceSource(asset="rai-rai-reflex-index", currency="usd"),
            UniswapV3PriceSource(asset="rai", currency="usd"),
        ],
    ),
)

if __name__ == "__main__":
    price, _ = asyncio.run(rai_usd_median_feed.source.fetch_new_datapoint())
    print("rai/usd price:", price)
