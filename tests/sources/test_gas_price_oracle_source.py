import os
from datetime import datetime
from time import time

import pytest
from telliot_core.apps.telliot_config import TelliotConfig
from telliot_core.model.endpoints import EndpointList
from telliot_core.model.endpoints import RPCEndpoint

from telliot_feeds.sources.gas_price_oracle import GasPriceOracleSource


@pytest.mark.asyncio
async def test_fetch_new_datapoint():
    """Retrieve historical gas price data from source."""

    timestamp = time() - 2000
    chain_id = 1
    cfg = TelliotConfig()
    custom_endpoint = RPCEndpoint(chain_id=1, url=f"https://mainnet.infura.io/v3/{os.environ['INFURA_API_KEY']}")

    cfg.endpoints = EndpointList(endpoints=[custom_endpoint])

    v, t = await GasPriceOracleSource(chainId=chain_id, timestamp=timestamp, cfg=cfg).fetch_new_datapoint()
    print(v)
    assert v is not None and t is not None
    assert isinstance(v, float)
    assert isinstance(t, datetime)
