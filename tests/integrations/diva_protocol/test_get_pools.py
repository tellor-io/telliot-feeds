"""
Get pools from DIVA subgraph.

Fetch new pools from the DIVA Protocol subgraph.
Filter out pools that have already been reported.
Filter out pools that have already been settled.
Filter out pools with unsupported reference assets or
unsupported collateral tokens."""
import datetime

import pytest

from telliot_feeds.integrations.diva_protocol import DIVA_TELLOR_MIDDLEWARE_ADDRESS
from telliot_feeds.integrations.diva_protocol.pool import fetch_from_subgraph
from telliot_feeds.integrations.diva_protocol.pool import query_valid_pools


# int timestamp of yesterday
yesterday = int(datetime.datetime.now().timestamp() - 60 * 60 * 24)
# int timestamp of today's date
sep_20_2022 = int(datetime.datetime(2022, 9, 20).timestamp())


@pytest.mark.asyncio
async def test_get_pools_from_subgraph():
    query = query_valid_pools(
        last_id=0,
        data_provider=DIVA_TELLOR_MIDDLEWARE_ADDRESS,
        expiry_since=sep_20_2022,
    )
    pools = await fetch_from_subgraph(
        query=query,
        network="goerli",
    )

    print(pools)
    assert pools is not None
    assert isinstance(pools, list)
    if len(pools) > 0:
        assert isinstance(pools[0], dict)
        assert "id" in pools[0]
        assert "referenceAsset" in pools[0]
        assert "collateralBalance" in pools[0]
        assert "expiryTime" in pools[0]
        assert "collateralToken" in pools[0]
        assert "id" in pools[0]["collateralToken"]
        assert "symbol" in pools[0]["collateralToken"]
