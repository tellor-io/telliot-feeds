from datetime import datetime

import pytest

from telliot_feed_examples.sources import diva_protocol
from telliot_feed_examples.sources.diva_protocol import DivaManualSource


@pytest.mark.asyncio
async def test_uspce_source():
    """Test retrieving USPCE data from user input."""
    # Override Python built-in input method
    diva_protocol.input = lambda: "1234.5678"

    source = DivaManualSource(reference_asset="BTC/USD", timestamp=0)

    val, dt = await source.fetch_new_datapoint()

    assert isinstance(dt, datetime)
    assert dt.year == 1970
    assert val == 1234.5678
