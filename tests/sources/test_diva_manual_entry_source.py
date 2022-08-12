from datetime import datetime

import pytest

from unittest import mock

from telliot_feeds.sources.manual_sources.diva_manual_source import DivaManualSource


@pytest.mark.asyncio
async def test_source():
    """Test retrieving DIVA Protocol query response from user input."""
    with mock.patch("builtins.input", side_effect=["-1234", "1234", "5678", ""]):
        source = DivaManualSource()
        val, dt = await source.fetch_new_datapoint()

        assert isinstance(dt, datetime)
        assert val == [1234, 5678]
