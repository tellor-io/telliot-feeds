import statistics

import pytest

from telliot_feeds.feeds.wrseth_usd_feed import wrseth_usd_feed


@pytest.mark.asyncio
async def test_wrseth_usd_feed(caplog):
    """Retrieve median WrsETH/USD price."""
    v, _ = await wrseth_usd_feed.source.fetch_new_datapoint()

    assert v is not None
    assert v > 0
    assert "sources used in aggregate: 4" in caplog.text.lower()
    print(f"WrsETH/USD Price: {v}")
    # Get list of data sources from sources dict
    source_prices = wrseth_usd_feed.source.latest[0]

    # Make sure error is less than decimal tolerance
    assert (v - statistics.median([source_prices])) < 10**-6
