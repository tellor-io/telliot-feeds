import pytest

from telliot_ampl_feeds.scripts import submit_uspce
from telliot_ampl_feeds.scripts.submit_uspce import submit


@pytest.mark.asyncio
async def test_submit_value(cfg, master, oracle):
    """Test submitting USPCE value to TellorX oracle."""
    # Override Python built-in input method
    submit_uspce.input = lambda: "1234.1234"

    status = await submit(cfg, master, oracle)

    assert status.ok
