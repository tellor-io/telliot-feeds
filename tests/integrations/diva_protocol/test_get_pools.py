"""
Get pools from DIVA subgraph.

Fetch new pools from the DIVA Protocol subgraph.
Filter out pools that have already been reported.
Filter out pools that have already been settled.
Filter out pools with unsupported reference assets or
unsupported collateral tokens."""
import datetime

import pytest

from telliot_feeds.integrations.diva_protocol.pool import fetch_from_subgraph
from telliot_feeds.integrations.diva_protocol.pool import query_valid_pools

# from telliot_feeds.integrations.diva_protocol import DIVA_TELLOR_MIDDLEWARE_ADDRESS


# int timestamp of yesterday
yesterday = int(datetime.datetime.now().timestamp() - 60 * 60 * 24)
# int timestamp of one month ago
one_month_ago = int(datetime.datetime.now().timestamp() - 60 * 60 * 24 * 30)
network = "mumbai"
# data_provider = DIVA_TELLOR_MIDDLEWARE_ADDRESS
# todo: report some w/ Tellor, so can use middleware address instead
data_provider = "0x9adefeb576dcf52f5220709c1b267d89d5208d78"


@pytest.mark.asyncio
async def test_get_pools_from_subgraph():
    query = query_valid_pools(
        data_provider=data_provider,
        expiry_since=one_month_ago,
    )
    pools = await fetch_from_subgraph(
        query=query,
        network=network,
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
