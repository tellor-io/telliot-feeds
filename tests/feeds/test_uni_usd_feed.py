import statistics

import pytest

from telliot_feeds.feeds.uni_usd_feed import uni_usd_median_feed


@pytest.mark.asyncio
async def test_uni_usd_median_feed(caplog, mock_price_feed):
    """Retrieve median uni/USD price."""
    mock_prices = [1200.50, 1205.25, 1202.75]
    mock_price_feed(uni_usd_median_feed, mock_prices)
    v, _ = await uni_usd_median_feed.source.fetch_new_datapoint()

    assert v is not None
    assert v > 0
    assert "sources used in aggregate: 3" in caplog.text.lower()
    print(f"uni/USD Price: {v}")

    # Get list of data sources from sources dict
    source_prices = [source.latest[0] for source in uni_usd_median_feed.source.sources]
    print(source_prices)

    # Make sure error is less than decimal tolerance
    assert (v - statistics.median(source_prices)) < 10**-6
