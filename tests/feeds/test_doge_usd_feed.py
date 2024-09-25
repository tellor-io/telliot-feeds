import statistics

import pytest

from telliot_feeds.feeds.doge_usd_feed import doge_usd_median_feed


@pytest.mark.asyncio
async def test_doge_usd_median_feed(caplog):
    """Retrieve median doge/USD price."""
    v, _ = await doge_usd_median_feed.source.fetch_new_datapoint()

    assert v is not None
    assert v > 0
    assert "sources used in aggregate: 3" in caplog.text.lower()
    print(f"doge/USD Price: {v}")

    # Get list of data sources from sources dict
    source_prices = [source.latest[0] for source in doge_usd_median_feed.source.sources]
    print(source_prices)

    # Make sure error is less than decimal tolerance
    assert (v - statistics.median(source_prices)) < 10**-6
