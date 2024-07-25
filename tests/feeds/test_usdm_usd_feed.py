import statistics

import pytest

from telliot_feeds.feeds.usdm_usd_feed import usdm_usd_median_feed


@pytest.mark.asyncio
async def test_usdm_usd_median_feed(caplog):
    """Retrieve median USDM/USD price."""
    v, _ = await usdm_usd_median_feed.source.fetch_new_datapoint()

    assert v is not None
    assert v > 0
    assert "sources used in aggregate: 2" in caplog.text.lower()
    print(f"USDM/ETH Price: {v}")
    # Get list of data sources from sources dict
    source_prices = usdm_usd_median_feed.source.latest[0]

    # Make sure error is less than decimal tolerance
    assert (v - statistics.median([source_prices])) < 10**-6
