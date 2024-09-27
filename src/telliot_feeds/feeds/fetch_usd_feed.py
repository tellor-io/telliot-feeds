"""Datafeed for current price of FETCH in USD."""
from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.pulsex_subgraph import PulseXSubgraphSource
from telliot_feeds.sources.price.spot.fetch_usd_mock import FetchUsdMockSpotPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator
#from telliot_feeds.sources.price.spot.pulsex_fetch_dai import PulseXFETCHDAISource
from dotenv import load_dotenv
import os

load_dotenv()

if os.getenv("FETCH_USD_MOCK_PRICE"):
    fetch_usd_median_feed = DataFeed(
        query=SpotPrice(asset="fetch", currency="usd"),
        source=FetchUsdMockSpotPriceSource(asset="fetch", currency="usd")
        )
        
else:
    fetch_usd_median_feed = DataFeed(
        query=SpotPrice(asset="fetch", currency="usd"),
        source=PriceAggregator(
            asset="fetch",
            currency="usd",
            algorithm="median",
            sources=[PulseXSubgraphSource(asset="fetch", currency="usd")],
        )
    )
