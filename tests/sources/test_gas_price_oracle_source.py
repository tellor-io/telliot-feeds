from datetime import datetime
from time import time

import pytest

from telliot_feeds.sources.gas_price_oracle import GasPriceOracleSource


@pytest.mark.skip("TODO: Fix")
@pytest.mark.asyncio
async def test_fetch_new_datapoint():
    """Retrieve historical gas price data from source."""

    timestamp = time() - 2000
    chain_id = 1

    v, t = await GasPriceOracleSource(chain_id=chain_id, timestamp=timestamp).fetch_new_datapoint()

    assert v is not None and t is not None
    assert isinstance(v, float)
    assert isinstance(t, datetime)
