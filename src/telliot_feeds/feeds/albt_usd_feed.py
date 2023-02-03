import asyncio

from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.coinmarketcap import (
    CoinMarketCapSpotPriceSource,
)
from telliot_feeds.sources.price_aggregator import PriceAggregator

albt_usd_median_feed = DataFeed(
    query=SpotPrice(asset="ALBT", currency="USD"),
    source=PriceAggregator(
        asset="albt",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="albt", currency="usd"),
            CoinMarketCapSpotPriceSource(asset="albt", currency="usd"),
        ],
    ),
)


if __name__ == "__main__":
    # Run this script to see the median price of ALBT/USD
    price, ts = asyncio.run(albt_usd_median_feed.source.fetch_new_datapoint())
    print(f"ALBT/USD: {price} @ {ts}")
