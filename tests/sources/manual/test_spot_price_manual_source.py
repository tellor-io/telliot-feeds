from unittest import mock

import pytest

from telliot_feeds.sources.manual.spot_price_input_source import SpotPriceManualSource
from telliot_feeds.utils.log import get_logger

logger = get_logger(__name__)


@pytest.mark.asyncio
async def test_manual_spot_price_good_input():
    with mock.patch("telliot_feeds.utils.input_timeout.InputTimeout.__call__", side_effect=["1234", ""]):
        result, _ = await SpotPriceManualSource().fetch_new_datapoint()
        assert result == 1234


@pytest.mark.asyncio
async def test_manual_spot_price_bad_input(capsys):
    with mock.patch("telliot_feeds.utils.input_timeout.InputTimeout.__call__", side_effect=["float", "5678", ""]):
        result, _ = await SpotPriceManualSource().fetch_new_datapoint()
        expected = "Invalid input. Enter decimal value (float)."
        captured_output = capsys.readouterr()
        assert expected in captured_output.out.strip()
        assert type(result) is float
        assert result == 5678
