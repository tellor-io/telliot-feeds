import statistics

import pytest

from telliot_feeds.feeds.usn_usd_feed import usn_usd_median_feed


@pytest.mark.asyncio
async def test_usn_usd_median_feed(mock_price_feed, caplog):
    """Retrieve median USN/USD price."""
    mock_prices = [1.01, 1.10]
    mock_price_feed(usn_usd_median_feed, mock_prices)
    v, _ = await usn_usd_median_feed.source.fetch_new_datapoint()

    assert v is not None
    assert v > 0
    assert "sources used in aggregate: 2" in caplog.text.lower()
    print(f"USN/USD Price: {v}")

    # Get list of data sources from sources dict
    source_prices = [source.latest[0] for source in usn_usd_median_feed.source.sources]
    print(source_prices)

    # Make sure error is less than decimal tolerance
    assert (v - statistics.median(source_prices)) < 10**-6
