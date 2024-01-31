import statistics

import pytest

from telliot_feeds.feeds.wsteth_feed import wsteth_eth_median_feed


@pytest.mark.asyncio
async def test_wsteth_eth_median_feed(caplog):
    """Retrieve median WSTETH/ETH price."""
    v, _ = await wsteth_eth_median_feed.source.fetch_new_datapoint()

    assert v is not None
    assert v > 0
    assert "sources used in aggregate: 4" in caplog.text.lower()
    print(f"WSTETH/ETH Price: {v}")
    # Get list of data sources from sources dict
    source_prices = wsteth_eth_median_feed.source.latest[0]

    # Make sure error is less than decimal tolerance
    assert (v - statistics.median([source_prices])) < 10**-6
