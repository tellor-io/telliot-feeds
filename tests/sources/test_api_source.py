from datetime import datetime

import pytest

from telliot_feed_examples.sources.api_source import APIQuerySource


# test different apis with different outputs to test parser capabilities


@pytest.mark.asyncio
async def test_weather():
    ex_url_1 = (
        "https://samples.openweathermap.org/data/2.5/weather?q=Lond`on," "uk&appid=b6907d289e10d714a6e88b30761fae22"
    )
    ex_key_1 = "id, temp_min, clouds"
    weather_query = APIQuerySource(url=ex_url_1, key_str=ex_key_1)
    resp = weather_query.main_parser()
    exp_response = [[300, 5091, 2643743], 279.15, {"all": 90}]
    assert resp == exp_response


@pytest.mark.asyncio
async def test_activity():
    ex_url_2 = "https://www.boredapi.com/api/activity"
    ex_key_2 = "activity"
    activity_query = APIQuerySource(url=ex_url_2, key_str=ex_key_2)
    resp = activity_query.main_parser()
    assert isinstance(resp[0], str)


@pytest.mark.asyncio
async def test_ts():
    ex_url_3 = "https://taylorswiftapi.herokuapp.com/get"
    ex_key_3 = "album"
    ts_query = APIQuerySource(url=ex_url_3, key_str=ex_key_3)
    resp = ts_query.main_parser()
    album_list = [
        "Taylor Swift",
        "Fearless",
        "Speak Now",
        "Red",
        "1989",
        "Reputation",
        "Lover",
        "Folklore",
        "Evermore",
    ]
    assert resp[0] in album_list


@pytest.mark.asyncio
async def test_coindesk():
    ex_url_4 = "https://api.coindesk.com/v1/bpi/currentprice.json"
    ex_key_4 = "USD, rate_float"
    coindesk_query = APIQuerySource(url=ex_url_4, key_str=ex_key_4)
    resp = coindesk_query.main_parser()
    assert resp[0]["rate_float"] == resp[1][0]


@pytest.mark.asyncio
async def test_cat():
    ex_url_5 = "https://catfact.ninja/fact"
    ex_key_5 = ""
    cat_query = APIQuerySource(url=ex_url_5, key_str=ex_key_5)
    resp = cat_query.main_parser()
    assert isinstance(resp, str)


@pytest.mark.asyncio
async def test_gas():
    ex_url_6 = "https://api.collectapi.com/gasPrice/turkeyGasoline?" "district=kadikoy&city=istanbul"
    ex_key_6 = ""
    gas_query = APIQuerySource(url=ex_url_6, key_str=ex_key_6)
    resp = gas_query.main_parser()
    assert resp == "null"


@pytest.mark.asyncio
async def test_full():
    ex_url_1 = (
        "https://samples.openweathermap.org/data/2.5/weather?q=Lond`on," "uk&appid=b6907d289e10d714a6e88b30761fae22"
    )
    ex_key_1 = "id, temp_min, clouds"
    weather_query = APIQuerySource(url=ex_url_1, key_str=ex_key_1)
    val, dt = await weather_query.fetch_new_datapoint()

    assert val == "[[300, 5091, 2643743], 279.15, {'all': 90}]"
    assert isinstance(val, str)
    assert isinstance(dt, datetime)
