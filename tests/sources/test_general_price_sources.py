""" Unit tests for pricing module

"""
import os
from datetime import datetime

import pytest
from telliot_core.apps.telliot_config import TelliotConfig

from telliot_feed_examples.sources.bittrex import BittrexPriceService
from telliot_feed_examples.sources.coinbase import CoinbasePriceService
from telliot_feed_examples.sources.coingecko import CoinGeckoPriceService
from telliot_feed_examples.sources.gemini import GeminiPriceService
from telliot_feed_examples.sources.nomics import NomicsPriceService
from telliot_feed_examples.sources.pancakeswap_usd import PancakeswapPriceService
from telliot_feed_examples.sources.uniswapV3_usd import UniswapV3PriceService


service = {
    "coinbase": CoinbasePriceService(),
    "coingecko": CoinGeckoPriceService(),
    "bittrex": BittrexPriceService(),
    "gemini": GeminiPriceService(),
    "nomics": NomicsPriceService(),
    "uniswapV3": UniswapV3PriceService(),
    "pancakeswap": PancakeswapPriceService(),
}


async def get_price(asset, currency, s):
    """Helper function for retrieving prices."""
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
        print("No Nomics api key ")


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
    """Test retrieving from UniswapV3 price source."""
    v, t = await get_price("wbtc", "usd", service["uniswapV3"])
    validate_price(v, t)


@pytest.mark.asyncio
async def test_pancakeswap_usd():
    """Test retrieving from UniswapV3 price source."""
    v, t = await get_price("wbnb", "usd", service["pancakeswap"])
    validate_price(v, t)


# def test_web_price_service_timeout():
#     ps = CoinbasePriceService(timeout=0.0000001)
#     result = ps.get_url()
#     assert result["error"] == "Timeout Error"
