from datetime import datetime

import pytest

from telliot_feeds.sources.price.historical.cryptowatch import (
    CryptowatchHistoricalPriceService,
)
from telliot_feeds.sources.price.historical.kraken import (
    KrakenHistoricalPriceService,
)
from telliot_feeds.sources.price.historical.poloniex import (
    PoloniexHistoricalPriceService,
)


def isfloat(num: str) -> bool:
    """Check if string is numeric."""
    try:
        float(num)
        return True
    except ValueError:
        return False


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


@pytest.mark.asyncio
async def test_kraken_get_price():
    """Retrieve singular price close to given timestamp."""
    v, t = await KrakenHistoricalPriceService().get_price("eth", "usd", ts=1616663420)
    validate_price(v, t)

    v, t = await KrakenHistoricalPriceService().get_price("xbt", "usd", ts=1616663420)
    validate_price(v, t)


@pytest.mark.asyncio
async def test_kraken_get_trades():
    """Retrieve all price data given a timestamp and surrounding time period."""
    six_hours = 60 * 60 * 6  # seconds
    trades, t = await KrakenHistoricalPriceService().get_trades(
        "eth",
        "usd",
        period=six_hours,
        ts=1647782323,
    )

    assert isinstance(t, datetime)
    assert isinstance(trades, list)
    assert len(trades) > 0
    assert isfloat(trades[0][0])
    print("# trades in six hour window:", len(trades))

    trades, t = await KrakenHistoricalPriceService().get_trades(
        "xbt",
        "usd",
        period=six_hours,
        ts=1647782323,
    )

    assert isinstance(t, datetime)
    assert isinstance(trades, list)
    assert len(trades) > 0
    assert isfloat(trades[0][0])
    print("# trades in six hour window:", len(trades))


@pytest.mark.asyncio
async def test_poloniex_get_price():
    """Retrieve single historical price close to given timestamp."""
    six_hours = 60 * 60 * 6  # seconds
    v, t = await PoloniexHistoricalPriceService().get_price("eth", "tusd", period=six_hours, ts=1647782323)
    validate_price(v, t)

    # Returns {"code": 500, "message": "System error"} for dai...
    # v, t = await PoloniexHistoricalPriceService().get_price("eth", "dai", ts=1645822159)
    # validate_price(v, t)

    # v, t = await PoloniexHistoricalPriceService().get_price("btc", "dai", ts=1645813159)
    # validate_price(v, t)

    v, t = await PoloniexHistoricalPriceService().get_price("btc", "tusd", ts=1645822159)
    validate_price(v, t)


@pytest.mark.asyncio
async def test_poloniex_get_trades():
    """Retrieve all price data given a timestamp and surrounding time period."""
    six_hours = 60 * 60 * 6  # seconds
    trades, t = await PoloniexHistoricalPriceService().get_trades(
        "eth",
        "tusd",
        period=six_hours,
        ts=1647782323,
    )

    assert isinstance(t, datetime)
    assert isinstance(trades, list)
    assert len(trades) > 0
    assert isfloat(trades[0]["rate"])
    print("# trades in six hour window:", len(trades))

    trades, t = await PoloniexHistoricalPriceService().get_trades(
        "btc",
        "tusd",
        period=six_hours,
        ts=1647782323,
    )

    assert isinstance(t, datetime)
    assert isinstance(trades, list)
    assert len(trades) > 0
    assert isfloat(trades[0]["rate"])
    print("# trades in six hour window:", len(trades))


@pytest.mark.skip("TODO: handle candle data for certain timestamps")
@pytest.mark.asyncio
async def test_cryptowatch_get_price():
    """Retrieve single historical price close to given timestamp."""
    v, t = await CryptowatchHistoricalPriceService().get_price("eth", "usd", ts=1648567107)
    validate_price(v, t)

    v, t = await CryptowatchHistoricalPriceService().get_price("btc", "usd", ts=1648567107)
    validate_price(v, t)


@pytest.mark.skip("TODO: handle candle data for certain timestamps")
@pytest.mark.asyncio
async def test_cryptowatch_get_candles():
    """Retrieve all price data given a timestamp and surrounding time period."""
    six_hours = 60 * 60 * 6  # seconds
    candles, t = await CryptowatchHistoricalPriceService().get_candles(
        "eth",
        "usd",
        period=six_hours,
        ts=1649252172,
    )

    assert isinstance(t, datetime)
    assert isinstance(candles, list)
    assert len(candles) > 0
    assert isfloat(candles[-1][4])
    print("# eth/usd candles in six hour window:", len(candles))

    candles, t = await CryptowatchHistoricalPriceService().get_candles(
        "btc",
        "usd",
        period=six_hours,
        ts=1648567107,
    )

    assert isinstance(t, datetime)
    assert isinstance(candles, list)
    assert len(candles) > 0
    assert isfloat(candles[-1][4])
    print("# btc/usd candles in six hour window:", len(candles))
