import statistics

import pytest

from telliot_feeds.feeds.weeth_usd_feed import weeth_usd_median_feed


@pytest.mark.asyncio
async def test_weeth_usd_median_feed(caplog):
    """Retrieve median weETH/USD price."""
    v, _ = await weeth_usd_median_feed.source.fetch_new_datapoint()

    assert v is not None
    assert v > 0
    assert "sources used in aggregate: 4" in caplog.text.lower()
    print(f"weETH/USD Price: {v}")
    # Get list of data sources from sources dict
    source_prices = weeth_usd_median_feed.source.latest[0]

    # Make sure error is less than decimal tolerance
    assert (v - statistics.median([source_prices])) < 10**-6
