# from datetime import datetime
import pytest

from telliot_feeds.sources.numeric_api_response import NumericApiResponseSource


# test different apis with different outputs to test parser capabilities


@pytest.mark.asyncio
async def test_weather():
    source = NumericApiResponseSource(
        url="https://samples.openweathermap.org/data/2.5/weather?q=Lond`on,uk&appid=b6907d289e10d714a6e88b30761fae22",
        parseStr="main, temp_min",
    )
    val, _ = await source.fetch_new_datapoint()
    assert val == 279.15


@pytest.mark.asyncio
async def test_coindesk():
    source = NumericApiResponseSource(
        url="https://api.coindesk.com/v1/bpi/currentprice.json",
        parseStr="bpi, USD, rate_float",
    )
    val, _ = await source.fetch_new_datapoint()
    assert 5000 < val < 100000


@pytest.mark.asyncio
async def test_gas():
    source = NumericApiResponseSource(
        url="https://api.collectapi.com/gasPrice/turkeyGasoline?district=kadikoy&city=istanbul",
        parseStr="",
    )
    val, _ = await source.fetch_new_datapoint()
    assert val is None


@pytest.mark.asyncio
async def test_full():
    source = NumericApiResponseSource(
        url="https://samples.openweathermap.org/data/2.5/weather?q=Lond`on,uk&appid=b6907d289e10d714a6e88b30761fae22",
        parseStr="weather, 0, id",
    )
    val, _ = await source.fetch_new_datapoint()
    assert val == 300
