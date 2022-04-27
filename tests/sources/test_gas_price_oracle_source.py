from datetime import datetime
from time import time

import pytest
from telliot_core.apps.telliot_config import TelliotConfig

from telliot_feed_examples.sources.gas_price_oracle import GasPriceOracleSource


@pytest.mark.asyncio
@pytest.mark.skip
async def test_fetch_new_datapoint():
    """Retrieve historical gas price data from source."""

    api_key = TelliotConfig().api_keys.find(name="owlracle")[0].key
    timestamp = time() - 2000
    chain_id = 1

    v, t = await GasPriceOracleSource().fetch_new_datapoint(
        api_key, timestamp, chain_id
    )

    assert v is not None and t is not None
    assert isinstance(v, float)
    assert isinstance(t, datetime)


EXAMPLE_RESPONSE = 31.8
