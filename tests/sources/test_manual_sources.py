from unittest import mock

import pytest

from telliot_feeds.sources.manual_sources.spot_price_input_source import SpotPriceManualSource
from telliot_feeds.sources.manual_sources.string_query_manual_source import StringQueryManualSource
from telliot_feeds.utils.log import get_logger

logger = get_logger(__name__)


@pytest.mark.asyncio
async def test_manual_spot_price_good_input(
    monkeypatch,
):
    monkeypatch.setattr("builtins.input", lambda: "1234")
    result, _ = await SpotPriceManualSource().fetch_new_datapoint()
    assert result == 1234


@pytest.mark.asyncio
async def test_manual_spot_price_bad_input(capsys):
    with mock.patch("builtins.input", side_effect=["float", "5678", ""]):
        result, _ = await SpotPriceManualSource().fetch_new_datapoint()
        expected = "Invalid input. Enter decimal value (float)."
        captured_output = capsys.readouterr()
        assert expected in captured_output.out.strip()
        assert type(result) is float
        assert result == 5678


@pytest.mark.asyncio
async def test_string_query_good_input(capsys):
    inpt = "hello"
    with mock.patch("builtins.input", side_effect=[inpt, ""]):
        result, _ = await StringQueryManualSource().fetch_new_datapoint()
        assert isinstance(result, str)
        assert result == "hello"


@pytest.mark.asyncio
async def test_string_query_bad_input(capsys):
    with mock.patch("builtins.input", side_effect=[b"flat", "flat", ""]):
        await StringQueryManualSource().fetch_new_datapoint()
        expected = "Invalid input. use regular text! (Example input: the earth is flat, jk!)"
        captured_output = capsys.readouterr()
        assert expected in captured_output.out.strip()
