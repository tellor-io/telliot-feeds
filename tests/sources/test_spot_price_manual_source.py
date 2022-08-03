from unittest import mock

import pytest

from telliot_feeds.sources.manual_sources.spot_price_input_source import SpotPriceManualSource
from telliot_feeds.utils.log import get_logger

logger = get_logger(__name__)


@pytest.mark.asyncio
async def test_manual_spot_price(
    monkeypatch,
):
    monkeypatch.setattr("builtins.input", lambda: "1234")
    result, _ = await SpotPriceManualSource().fetch_new_datapoint()
    assert result == 1234


@pytest.mark.asyncio
async def test_bad_user_input():
    with mock.patch("builtins.input", side_effect=["float", "5678", ""]):
        result, _ = await SpotPriceManualSource().fetch_new_datapoint()
        assert type(result) is float
        assert result == 5678
