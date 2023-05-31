import statistics

import pytest

from telliot_feeds.feeds.cny_usd_feed import cny_usd_median_feed


@pytest.mark.asyncio
async def test_cny_usd_median_feed():
    """Retrieve median CNY/USD price."""
    v, _ = await cny_usd_median_feed.source.fetch_new_datapoint()

    assert v is not None
    assert v > 0
    print(f"CNY/USD Price: {v}")

    # Get list of data sources from sources dict
    source_prices = [source.latest[0] for source in cny_usd_median_feed.source.sources]
    print(source_prices)

    # Make sure error is less than decimal tolerance
    assert (v - statistics.median(source_prices)) < 10**-6
