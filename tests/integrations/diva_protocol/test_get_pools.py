"""
Get pools from DIVA subgraph.

Fetch new pools from the DIVA Protocol subgraph.
Filter out pools that have already been reported.
Filter out pools that have already been settled.
Filter out pools with unsupported reference assets or
unsupported collateral tokens."""
import pytest

from telliot_feeds.integrations.diva_protocol.pool import fetch_from_subgraph
from telliot_feeds.integrations.diva_protocol.pool import query_valid_pools


# centralized oracle ran by DIVA Protocol team
DIVA_ORACLE = "0x245b8abbc1b70b370d1b81398de0a7920b25e7ca"


@pytest.mark.asyncio
async def test_get_pools_from_subgraph():
    query = query_valid_pools(
        last_id=49100,
        data_provider=DIVA_ORACLE,
        expiry_since=1658845000,
    )
    pools = await fetch_from_subgraph(
        query=query,
        network="ropsten",
    )

    # print(pools)
    assert pools is not None
    assert isinstance(pools, list)
    assert len(pools) > 0
    assert isinstance(pools[0], dict)
    assert "id" in pools[0]
    assert "referenceAsset" in pools[0]
    assert "collateralBalance" in pools[0]
    assert "expiryTime" in pools[0]
    assert "collateralToken" in pools[0]
    assert "id" in pools[0]["collateralToken"]
    assert "symbol" in pools[0]["collateralToken"]
