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


ONE_DAY_AGO_TIMESTAMP = int(datetime.now().timestamp()) - 86400
SIX_HOURS_SECONDS = 21600


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
async def test_kraken_get_price(caplog):
    """Retrieve singular price close to given timestamp."""
    v, t = await KrakenHistoricalPriceService(timeout=3).get_price("eth", "usd", ts=ONE_DAY_AGO_TIMESTAMP)
    validate_price(v, t)

    v, t = await KrakenHistoricalPriceService(timeout=3).get_price("xbt", "usd", ts=ONE_DAY_AGO_TIMESTAMP)
    validate_price(v, t)

    print("Kraken XBT/USD price:", v)


@pytest.mark.skip(reason="get trades tested in get price")
@pytest.mark.asyncio
async def test_kraken_get_trades(caplog):
    """Retrieve all price data given a timestamp and surrounding time period."""
    # Test invalid currency
    trades, t = await KrakenHistoricalPriceService().get_trades(
        asset="eth", currency="invalid", period=SIX_HOURS_SECONDS, ts=ONE_DAY_AGO_TIMESTAMP
    )
    assert trades is None
    assert t is None
    assert "Currency not supported" in caplog.text

    trades, t = await KrakenHistoricalPriceService().get_trades(
        "eth",
        "usd",
        period=SIX_HOURS_SECONDS,
        ts=ONE_DAY_AGO_TIMESTAMP,
    )

    assert isinstance(t, datetime)
    assert isinstance(trades, list)
    assert len(trades) > 0
    assert isfloat(trades[0][0])
    # print("# trades in six hour window:", len(trades))

    trades, t = await KrakenHistoricalPriceService().get_trades(
        "xbt",
        "usd",
        period=SIX_HOURS_SECONDS,
        ts=ONE_DAY_AGO_TIMESTAMP,
    )

    assert isinstance(t, datetime)
    assert isinstance(trades, list)
    assert len(trades) > 0
    assert isfloat(trades[0][0])
    # print("# trades in six hour window:", len(trades))


@pytest.mark.asyncio
async def test_poloniex_get_price():
    """Retrieve single historical price close to given timestamp."""
    v, t = await PoloniexHistoricalPriceService().get_price(
        "eth", "tusd", period=SIX_HOURS_SECONDS, ts=ONE_DAY_AGO_TIMESTAMP
    )
    validate_price(v, t)

    # Returns {"code": 500, "message": "System error"} for dai...
    # v, t = await PoloniexHistoricalPriceService().get_price("eth", "dai", ts=1645822159)
    # validate_price(v, t)

    # v, t = await PoloniexHistoricalPriceService().get_price("btc", "dai", ts=1645813159)
    # validate_price(v, t)

    # print("Poloniex BTC/DAI price:", v)

    v, t = await PoloniexHistoricalPriceService().get_price("btc", "tusd", ts=ONE_DAY_AGO_TIMESTAMP)
    validate_price(v, t)

    print("Poloniex BTC/TUSD price:", v)


@pytest.mark.asyncio
async def test_poloniex_get_trades():
    """Retrieve all price data given a timestamp and surrounding time period."""
    trades, t = await PoloniexHistoricalPriceService().get_trades(
        "eth",
        "tusd",
        period=SIX_HOURS_SECONDS,
        ts=ONE_DAY_AGO_TIMESTAMP,
    )

    assert isinstance(t, datetime)
    assert isinstance(trades, list)
    assert len(trades) > 0
    assert isfloat(trades[0]["rate"])
    # print("# trades in six hour window:", len(trades))

    trades, t = await PoloniexHistoricalPriceService().get_trades(
        "btc",
        "tusd",
        period=SIX_HOURS_SECONDS,
        ts=ONE_DAY_AGO_TIMESTAMP,
    )

    assert isinstance(t, datetime)
    assert isinstance(trades, list)
    assert len(trades) > 0
    assert isfloat(trades[0]["rate"])
    # print("# trades in six hour window:", len(trades))


@pytest.mark.asyncio
async def test_cryptowatch_get_price():
    """Retrieve single historical price close to given timestamp."""
    v, t = await CryptowatchHistoricalPriceService().get_price("eth", "usd", ts=ONE_DAY_AGO_TIMESTAMP)
    validate_price(v, t)

    v, t = await CryptowatchHistoricalPriceService().get_price("btc", "usd", ts=ONE_DAY_AGO_TIMESTAMP)
    validate_price(v, t)

    print("CryptoWatch BTC/USD last candle price:", v)


@pytest.mark.asyncio
async def test_cryptowatch_get_candles():
    """Retrieve all price data given a timestamp and surrounding time period."""
    candles, t = await CryptowatchHistoricalPriceService().get_candles(
        "eth",
        "usd",
        period=SIX_HOURS_SECONDS,
        ts=ONE_DAY_AGO_TIMESTAMP,
    )

    assert isinstance(t, datetime)
    assert isinstance(candles, list)
    assert len(candles) > 0
    assert isfloat(candles[-1][4])
    # print("# eth/usd candles in six hour window:", len(candles))

    candles, t = await CryptowatchHistoricalPriceService().get_candles(
        "btc",
        "usd",
        period=SIX_HOURS_SECONDS,
        ts=ONE_DAY_AGO_TIMESTAMP,
    )

    assert isinstance(t, datetime)
    assert isinstance(candles, list)
    assert len(candles) > 0
    assert isfloat(candles[-1][4])
    # print("# btc/usd candles in six hour window:", len(candles))
