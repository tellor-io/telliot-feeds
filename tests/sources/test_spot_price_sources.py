""" Unit tests for pricing module

"""
import os
from datetime import datetime

import pytest
from telliot_core.apps.telliot_config import TelliotConfig

from telliot_feed_examples.sources.price.spot.bittrex import BittrexSpotPriceService
from telliot_feed_examples.sources.price.spot.coinbase import CoinbaseSpotPriceService
from telliot_feed_examples.sources.price.spot.coingecko import CoinGeckoSpotPriceService
from telliot_feed_examples.sources.price.spot.gemini import GeminiSpotPriceService
from telliot_feed_examples.sources.price.spot.nomics import NomicsSpotPriceService
from telliot_feed_examples.sources.price.spot.pancakeswap import (
    PancakeswapPriceService,
)
from telliot_feed_examples.sources.price.spot.uniswapV3 import UniswapV3PriceService


service = {
    "coinbase": CoinbaseSpotPriceService(),
    "coingecko": CoinGeckoSpotPriceService(),
    "bittrex": BittrexSpotPriceService(),
    "gemini": GeminiSpotPriceService(),
    "nomics": NomicsSpotPriceService(),
    "pancakeswap": PancakeswapPriceService(),
    "uniswapV3": UniswapV3PriceService(),
}


async def get_price(asset, currency, s, timeout=10.0):
    """Helper function for retrieving prices."""
    s.timeout = timeout
    v, t = await s.get_price(asset, currency)
    return v, t


def validate_price(v, t):
    """Check types and price anomalies."""
    assert v is not None
    assert isinstance(v, float)
    assert v > 0
    assert isinstance(t, datetime)
    print(v)
    print(t)


@pytest.fixture()
def nomics_key():
    key = TelliotConfig().api_keys.find(name="nomics")[0].key

    if not key and "NOMICS_KEY" in os.environ:
        key = os.environ["NOMICS_KEY"]

    return key


@pytest.fixture()
def coinmarketcap_key():
    key = TelliotConfig().api_keys.find(name="coinmarketcap")[0].key

    if not key and "COINMARKETCAP_KEY" in os.environ:
        key = os.environ["COINMARKETCAP_KEY"]

    return key


@pytest.mark.asyncio
async def test_coinbase():
    """Test retrieving from Coinbase price source."""
    v, t = await get_price("btc", "usd", service["coinbase"])
    validate_price(v, t)


@pytest.mark.asyncio
async def test_coingecko():
    """Test retrieving from Coingecko price source."""
    v, t = await get_price("btc", "usd", service["coingecko"])
    validate_price(v, t)


@pytest.mark.asyncio
async def test_nomics(nomics_key):
    """Test retrieving from Nomics price source."""
    if nomics_key:
        v, t = await get_price("btc", "usd", service["nomics"])
        validate_price(v, t)
    else:
        print("No Nomics API key ")


@pytest.mark.asyncio
async def test_coinmarketcap(coinmarketcap_key):
    """Test retrieving from CoinMarketCap price source."""
    if coinmarketcap_key:
        v, t = await get_price("bct", "usd", service["coinmarketcap"])
        validate_price(v, t)
    else:
        print("No CoinMarketCap API key ")


@pytest.mark.asyncio
async def test_bittrex():
    """Test retrieving from Bittrex price source."""
    v, t = await get_price("btc", "usd", service["bittrex"])
    validate_price(v, t)


@pytest.mark.asyncio
async def test_gemini():
    """Test retrieving from Gemini price source."""
    v, t = await get_price("btc", "usd", service["gemini"])
    validate_price(v, t)


@pytest.mark.asyncio
async def test_uniswap_usd():
    """Test retrieving from UniswapV3 price source in USD."""
    v, t = await get_price("fuse", "usd", service["uniswapV3"])
    validate_price(v, t)


@pytest.mark.asyncio
async def test_uniswap_timeout():
    """Test retrieving from UniswapV3 price source in USD."""
    v, t = await get_price("fuse", "usd", service["uniswapV3"], 0.05)
    assert v is None
    assert t is None


@pytest.mark.asyncio
async def test_uniswap_eth():
    """Test retrieving from UniswapV3 price source in ETH."""
    v, t = await get_price("fuse", "eth", service["uniswapV3"])
    validate_price(v, t)


@pytest.mark.asyncio
async def test_uniswap_eth_usd():
    """Test retrieving from UniswapV3 price source for Eth in USD."""
    v, t = await get_price("eth", "usd", service["uniswapV3"])
    validate_price(v, t)


@pytest.mark.asyncio
async def test_pancakeswap_usd():
    """Test retrieving from Pancakeswap price source in USD."""
    v, t = await get_price("fuse", "usd", service["pancakeswap"])
    validate_price(v, t)


@pytest.mark.asyncio
async def test_pancakeswap_bnb():
    """Test retrieving from Pancakeswap price source in BNB."""
    v, t = await get_price("fuse", "bnb", service["pancakeswap"])
    validate_price(v, t)


# def test_web_price_service_timeout():
#     ps = CoinbaseSpotPriceService(timeout=0.0000001)
#     result = ps.get_url()
#     assert result["error"] == "Timeout Error"
