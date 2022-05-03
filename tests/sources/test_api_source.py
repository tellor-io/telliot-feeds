import pytest
from telliot_core.apps.telliot_config import TelliotConfig

from telliot_feed_examples.sources.api_source import APIQuerySource


### test 1


def test_api_weather():
    weather_url = "https://samples.openweathermap.org/data/2.5/weather?q=Lond`on,uk&appid=b6907d289e10d714a6e88b30761fae22"
    weather_args = "temp_min, description"

    exp_weather = [279.15, "light intensity drizzle"]

    weather_data = APIQuerySource(api_url=weather_url, arg_string=weather_args)

    assert exp_weather == weather_data
    assert isinstance(weather_data, list)


### test 2


### test 3
