from unittest import mock

import pytest

from telliot_feeds.sources.manual.twap_manual_input_source import TWAPManualSource


@pytest.mark.asyncio
async def test_manual_twap_positive_input():
    with mock.patch("telliot_feeds.utils.input_timeout.InputTimeout.__call__", side_effect=["1234", ""]):
        result, _ = await TWAPManualSource().fetch_new_datapoint()
        assert result == 1234


@pytest.mark.asyncio
async def test_manual_twap_negative_input(capsys):
    with mock.patch("telliot_feeds.utils.input_timeout.InputTimeout.__call__", side_effect=["-1234", "1234", ""]):
        result, _ = await TWAPManualSource().fetch_new_datapoint()
        expected = "Invalid input. Number must greater than 0."
        captured_output = capsys.readouterr()
        assert expected in captured_output.out.strip()
        assert type(result) is float
        assert result == 1234


@pytest.mark.asyncio
async def test_manual_twap_non_number_input(capsys):
    with mock.patch("telliot_feeds.utils.input_timeout.InputTimeout.__call__", side_effect=["hello", "1234", ""]):
        result, _ = await TWAPManualSource().fetch_new_datapoint()
        expected = "Invalid input. Enter a decimal value (float)."
        captured_output = capsys.readouterr()
        assert expected in captured_output.out.strip()
        assert type(result) is float
        assert result == 1234
