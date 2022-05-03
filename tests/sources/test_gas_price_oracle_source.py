from datetime import datetime
from time import time

import pytest

from telliot_feed_examples.sources.gas_price_oracle import GasPriceOracleSource


@pytest.mark.asyncio
async def test_fetch_new_datapoint():
    """Retrieve historical gas price data from source."""

    timestamp = time() - 2000
    chain_id = 1

    v, t = await GasPriceOracleSource().fetch_new_datapoint(timestamp, chain_id)

    assert v is not None and t is not None
    assert isinstance(v, float)
    assert isinstance(t, datetime)
