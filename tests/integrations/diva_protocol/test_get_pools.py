"""
Get pools from DIVA subgraph.

Fetch new pools from the DIVA Protocol subgraph.
Filter out pools that have already been reported.
Filter out pools that have already been settled.
Filter out pools with unsupported reference assets or
unsupported collateral tokens."""

import pytest


@pytest.mark.asyncio
async def test_get_pools_from_subgraph():
    pass


@pytest.mark.asyncio
async def test_fail_get_pools_from_subgraph():
    pass
