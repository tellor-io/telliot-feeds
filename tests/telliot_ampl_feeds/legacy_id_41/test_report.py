import pytest

from telliot_ampl_feeds.scripts import report_uspce
from telliot_ampl_feeds.scripts.report_uspce import report


@pytest.mark.asyncio
async def test_report_uspce(cfg, master, oracle):
    """Test submitting USPCE value to TellorX oracle."""
    # Override Python built-in input method
    report_uspce.input = lambda: "1234.1234"

    status = await report(cfg, master, oracle)

    assert status.ok
