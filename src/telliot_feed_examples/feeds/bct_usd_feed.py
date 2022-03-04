from telliot_core.datafeed import DataFeed
from telliot_core.queries import SpotPrice
from dotenv import load_dotenv
import os
from telliot_feed_examples.sources.coinmarketcap import CoinMarketCapPriceSource

from telliot_feed_examples.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feed_examples.sources.price.spot.nomics import NomicsSpotPriceSource
from telliot_feed_examples.sources.price_aggregator import PriceAggregator


load_dotenv(".../.env")


sources=[
    CoinGeckoSpotPriceSource(asset="bct", currency="usd"),
    NomicsSpotPriceSource(asset="bct", currency="usd"),
]

if 'CMC_API_KEY' in os.environ:
    CMC_API_KEY = os.getenv('CMC_API_KEY')
    sources.append(CoinMarketCapPriceSource(symbol = "BCT", key = ""))

bct_usd_median_feed = DataFeed(
    query=SpotPrice(asset="BCT", currency="USD"),
    source=PriceAggregator(
        asset="bct",
        currency="usd",
        algorithm="median",
        sources=sources,
    ),
)
