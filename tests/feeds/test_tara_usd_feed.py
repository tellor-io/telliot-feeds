import statistics

import pytest

from telliot_feeds.feeds.tara_usd_feed import tara_usd_median_feed


@pytest.mark.asyncio
async def test_tara_usd_median_feed(caplog):
    """Retrieve median TARA/USD price."""
    v, _ = await tara_usd_median_feed.source.fetch_new_datapoint()

    assert v is not None
    assert v > 0
    assert "sources used in aggregate: 2" in caplog.text.lower()
    print(f"TARA/ETH Price: {v}")
    # Get list of data sources from sources dict
    source_prices = tara_usd_median_feed.source.latest[0]

    # Make sure error is less than decimal tolerance
    assert (v - statistics.median([source_prices])) < 10**-6
