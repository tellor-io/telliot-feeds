from datetime import datetime

import pytest

from telliot_feeds.sources.evm_balance import EVMBalanceSource


@pytest.mark.asyncio
async def test_evm_balance():
    """Test that the EVM balance source returns the correct value."""
    evm_bal_source = EVMBalanceSource(
        chainId=11155111, evmAddress="0x210766226c54CDD6bD0401749D43E7a5585e3868", timestamp=1706302197
    )
    v, t = await evm_bal_source.fetch_new_datapoint()

    assert v == 2249577031885907390

    assert isinstance(v, int)
    assert isinstance(t, datetime)
