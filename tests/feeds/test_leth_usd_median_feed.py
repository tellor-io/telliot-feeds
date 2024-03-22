import statistics

import pytest

from telliot_feeds.feeds.leth_usd_feed import leth_usd_median_feed

@pytest.mark.asyncio
async def test_leth_usd_median_feed():
    """Retrieve median LETH/USD price"""
    v, _ = await leth_usd_median_feed.source.fetch_new_datapoint()

    assert v is not None
    assert v > 0
    print(f"LETH/USD price: {v}")