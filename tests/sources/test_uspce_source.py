from datetime import datetime

import pytest

from telliot_feed_examples.sources import uspce
from telliot_feed_examples.sources.uspce import USPCESource


@pytest.mark.asyncio
async def test_uspce_source():
    """Test retrieving USPCE data from user input."""
    # Override Python built-in input method
    uspce.input = lambda: "1234.1234"

    ampl_source = USPCESource()

    value, timestamp = await ampl_source.fetch_new_datapoint()

    assert isinstance(value, float)
    assert isinstance(timestamp, datetime)
    assert value > 0
