from datetime import datetime
from decimal import Decimal
from unittest import mock

import pytest

from telliot_feeds.sources.bea_gov import BEAPCESource
from telliot_feeds.sources.bea_gov import NIPA_TABLE_NAME
from telliot_feeds.sources.bea_gov import PCE_LINE_NUMBER


SAMPLE_RESPONSE = {
    "BEAAPI": {
        "Results": {
            "Data": [
                {"LineNumber": PCE_LINE_NUMBER, "TimePeriod": "2026M02", "DataValue": "126.200"},
                {"LineNumber": "2", "TimePeriod": "2026M03", "DataValue": "999.999"},
                {"LineNumber": PCE_LINE_NUMBER, "TimePeriod": "2026M01", "DataValue": "126.100"},
                {"LineNumber": PCE_LINE_NUMBER, "TimePeriod": "2025M12", "DataValue": "125.900"},
                {"LineNumber": PCE_LINE_NUMBER, "TimePeriod": "2026M03", "DataValue": "126.300"},
            ]
        }
    }
}


def test_calculate_3month_average():
    """Calculate the latest three-month PCE average from BEA rows."""
    source = BEAPCESource(api_key="test-key")

    assert source.calculate_3month_average(SAMPLE_RESPONSE) == Decimal("126.200000000000000000")


def test_calculate_3month_average_requires_three_values():
    """Return None when fewer than three PCE months are available."""
    source = BEAPCESource(api_key="test-key")
    response = {
        "BEAAPI": {
            "Results": {
                "Data": [
                    {"LineNumber": PCE_LINE_NUMBER, "TimePeriod": "2026M02", "DataValue": "126.200"},
                    {"LineNumber": PCE_LINE_NUMBER, "TimePeriod": "2026M03", "DataValue": "126.300"},
                ]
            }
        }
    }

    assert source.calculate_3month_average(response) is None


@pytest.mark.asyncio
async def test_fetch_new_datapoint():
    """Fetch BEA data and store the calculated USPCE datapoint."""
    response = mock.Mock()
    response.json.return_value = SAMPLE_RESPONSE
    session = mock.Mock()
    session.get.return_value = response
    session_context = mock.MagicMock()
    session_context.__enter__.return_value = session

    with mock.patch("telliot_feeds.sources.bea_gov.requests.Session", return_value=session_context):
        source = BEAPCESource(api_key="test-key")
        value, timestamp = await source.fetch_new_datapoint()

    assert value == Decimal("126.200000000000000000")
    assert isinstance(timestamp, datetime)
    assert source.latest[0] == value

    session.get.assert_called_once()
    call_kwargs = session.get.call_args.kwargs
    assert call_kwargs["params"]["UserID"] == "test-key"
    assert call_kwargs["params"]["TableName"] == NIPA_TABLE_NAME
    assert call_kwargs["params"]["LineNumber"] == PCE_LINE_NUMBER
    assert call_kwargs["params"]["Frequency"] == "M"
    assert call_kwargs["params"]["Year"] == "X"
