"""
Unit tests for currency exchange sources
ex. Coinbase's EUR/USD spot price
"""
from datetime import datetime

import pytest

from telliot_feeds.sources.price.currency.coinbase import CoinbaseCurrencyPriceService
from telliot_feeds.sources.price.currency.openexchangerate import OpenExchangeRateCurrencyPriceService


service = {"coinbase": CoinbaseCurrencyPriceService(), "open-exchange-rate": OpenExchangeRateCurrencyPriceService()}


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


@pytest.mark.asyncio
async def test_coinbase():
    v, t = await get_price("eur", "usd", service["coinbase"])
    validate_price(v, t)


@pytest.mark.asyncio
async def test_open_exchange_rate():
    v, t = await get_price("eur", "usd", service["open-exchange-rate"])
    validate_price(v, t)
