from decimal import Decimal
from unittest import mock

import pytest
import yaml

from telliot_feeds.feeds.uspce_feed import uspce_feed
from telliot_feeds.sources.bea_gov import BEAPCESource
from telliot_feeds.sources.bea_gov import PCE_LINE_NUMBER


SAMPLE_RESPONSE = {
    "BEAAPI": {
        "Results": {
            "Data": [
                {"LineNumber": PCE_LINE_NUMBER, "TimePeriod": "2026M01", "DataValue": "126.100"},
                {"LineNumber": PCE_LINE_NUMBER, "TimePeriod": "2026M02", "DataValue": "126.200"},
                {"LineNumber": PCE_LINE_NUMBER, "TimePeriod": "2026M03", "DataValue": "126.300"},
            ]
        }
    }
}


@pytest.mark.asyncio
async def test_uspce_feed():
    """Test USPCE feed."""
    feed = uspce_feed

    print(yaml.dump(feed.get_state(), sort_keys=False))
    assert isinstance(feed.source, BEAPCESource)

    with mock.patch.object(feed.source, "get_pce_data", return_value=SAMPLE_RESPONSE):
        value, timestamp = await feed.source.fetch_new_datapoint()

    print(f"USPCE report value: {value}")
    print(f"USPCE report timestamp: {timestamp}")

    assert value == Decimal("126.200000000000000000")
    assert timestamp is not None
