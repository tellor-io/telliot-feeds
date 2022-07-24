"""
Listen and filter for valid pools to report to.

Fetch new pools from the DIVA Protocol subgraph.
Filter out pools that have already been reported.
Filter out pools that have already been settled.
Filter out pools with unsupported reference assets or
unsupported collateral tokens."""

import pytest


@pytest.mark.asyncio
async def test_listen_new_pools():
    pass


@pytest.mark.asyncio
async def test_listen_new_pools_fail():
    pass


def test_filter_retrieved_pools():
    pass


def test_filter_retrieved_pools_fail():
    pass
