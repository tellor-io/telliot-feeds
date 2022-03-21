import pytest
from datetime import datetime

from telliot_feed_examples.sources.price.historical.cryptowatch import (
    CryptowatchHistoricalPriceService,
)
from telliot_feed_examples.sources.price.historical.kraken import (
    KrakenHistoricalPriceService,
)
from telliot_feed_examples.sources.price.historical.poloniex import (
    PoloniexHistoricalPriceService,
)


def isfloat(num: str) -> bool:
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
    v, t = await KrakenHistoricalPriceService().get_price("eth", "usd", ts=1616663420)
    validate_price(v, t)

    v, t = await KrakenHistoricalPriceService().get_price("xbt", "usd", ts=1616663420)
    validate_price(v, t)


@pytest.mark.asyncio
async def test_kraken_get_trades():
    six_hours = 60 * 60 * 6 # seconds
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


@pytest.mark.asyncio
async def test_poloniex_historical():
    v, t = await PoloniexHistoricalPriceService().get_price("eth", "dai", ts=1645813159)
    validate_price(v, t)

    v, t = await PoloniexHistoricalPriceService().get_price(
        "eth", "tusd", ts=1645822159
    )

    v, t = await PoloniexHistoricalPriceService().get_price("btc", "dai", ts=1645813159)
    validate_price(v, t)

    v, t = await PoloniexHistoricalPriceService().get_price(
        "btc", "tusd", ts=1645822159
    )


@pytest.mark.asyncio
async def test_cryptowatch_historical():
    v, t = await CryptowatchHistoricalPriceService().get_price(
        "eth", "usd", ts=1646145821
    )
    validate_price(v, t)

    v, t = await CryptowatchHistoricalPriceService().get_price(
        "btc", "usd", ts=1646145821
    )
    validate_price(v, t)