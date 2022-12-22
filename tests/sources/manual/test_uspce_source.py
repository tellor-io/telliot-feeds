from datetime import datetime
from unittest import mock

import pytest

from telliot_feeds.sources.manual.uspce import USPCESource


@pytest.mark.asyncio
async def test_uspce_source():
    """Test retrieving USPCE data from user input."""
    with mock.patch("telliot_feeds.utils.input_timeout.InputTimeout.__call__", side_effect=["1234.0", ""]):

        ampl_source = USPCESource()

        value, timestamp = await ampl_source.fetch_new_datapoint()

        assert isinstance(value, float)
        assert isinstance(timestamp, datetime)
        assert value > 0
