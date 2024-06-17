import statistics

import pytest

from telliot_feeds.feeds.tlos_usd_feed import tlos_usd_median_feed


@pytest.mark.asyncio
async def test_AssetPriceFeed():
    """Retrieve median TLOS price from example datafeed &
    make sure value is within tolerance."""
    # Fetch price
    # status, price, tstamp = await tlos_usd_median_feed.update_value()
    v, t = await tlos_usd_median_feed.source.fetch_new_datapoint()

    # Make sure error is less than decimal tolerance
    # assert status.ok
    assert v is not None
    assert v > 0
    assert "sources used in aggregate: 3" in caplog.text.lower()
    print(f"TLOS Price: {v}")

    # Get list of data sources from sources dict
    source_prices = [source.latest[0] for source in tlos_usd_median_feed.source.sources]

    # Make sure error is less than decimal tolerance
    assert (v - statistics.median(source_prices)) < 10**-6
