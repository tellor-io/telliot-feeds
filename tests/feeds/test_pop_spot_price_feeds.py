"""Tests for these spot price feeds:

AAVE/USD
AVAX/USD
BADGER/USD
BCH/USD
COMP/USD
CRV/USD
DOGE/USD
DOT/USD
EUL/USD
FIL/USD
GNO/USD
LINK/USD
LTC/USD
SHIB/USD
UNI/USD
USDT/USD
YFI/USD
"""
import pytest

from telliot_feeds.datafeed import DataFeed
from telliot_feeds.feeds import *  # noqa: F403, F401
from telliot_feeds.queries.price.spot_price import SpotPrice

# import DataFeed


@pytest.mark.asyncio
async def test_spot_price_feeds():
    """Test popular spot price feeds."""
    assets = [
        "AAVE",
        "AVAX",
        "BADGER",
        "BCH",
        "COMP",
        "CRV",
        "DOGE",
        "DOT",
        "EUL",
        "FIL",
        "GNO",
        "LINK",
        "LTC",
        "SHIB",
        "UNI",
        "USDT",
        "YFI",
    ]
    for name, obj in globals().items():
        if isinstance(obj, DataFeed) and isinstance(obj.query, SpotPrice):
            if obj.query.currency.lower() == "usd" and obj.query.asset.upper() in assets:
                print(f"Testing {name}")
                v, _ = await obj.source.fetch_new_datapoint()
                assert v > 0
                assets.pop(assets.index(obj.query.asset.upper()))

    assert len(assets) == 0
