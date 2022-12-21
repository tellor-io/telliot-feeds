from datetime import datetime
from unittest import mock

import pytest

from telliot_feeds.sources.manual_sources.diva_manual_source import DivaManualSource


@pytest.mark.asyncio
async def test_source(capsys):
    """Test retrieving DIVA Protocol query response from user input."""
    with mock.patch("builtins.input", side_effect=["-1234", "1234", "5678", ""]):
        source = DivaManualSource()
        val, dt = await source.fetch_new_datapoint()
        captured = capsys.readouterr()

        assert isinstance(dt, datetime)
        assert val == [1234, 5678]
        assert "[1234000000000000000000, 5678000000000000524288]" in captured.out
