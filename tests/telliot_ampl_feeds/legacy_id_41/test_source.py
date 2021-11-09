import os
from datetime import datetime

import pytest

from telliot_ampl_feeds.sources.uspce import USPCESource
from telliot_ampl_feeds.sources import uspce


@pytest.mark.asyncio
async def test_uspce_source():
    """Test retrieving USPCE data from user input."""
    # Override Python built-in input method
    uspce.input = lambda: "1234.1234"

    ampl_source = USPCESource()

    value, timestamp = await ampl_source.fetch_new_datapoint()
    print(value)

    assert isinstance(value, int)
    assert isinstance(timestamp, datetime)
    assert value > 0
