from datetime import datetime

import pytest

from telliot_feeds.sources.manual.diva_manual_source import DivaManualSource
from telliot_feeds.utils.input_timeout import InputTimeout


@pytest.mark.asyncio
async def test_source(capsys, monkeypatch):
    """Test retrieving DIVA Protocol query response from user input."""

    def mock_input(timeout=0, *args, **kwargs):
        return "1234.0\n"

    monkeypatch.setattr(InputTimeout, "__call__", mock_input)
    source = DivaManualSource()
    val, dt = await source.fetch_new_datapoint()
    captured = capsys.readouterr()

    assert isinstance(dt, datetime)
    assert val == [1234.0, 1234.0]
    assert "[1234000000000000000000, " in captured.out
