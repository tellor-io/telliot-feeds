import statistics

import pytest

from telliot_feeds.feeds.usdt_usd_feed import usdt_usd_median_feed


@pytest.mark.asyncio
async def test_usdt_usd_median_feed(caplog, mock_price_feed):
    """Retrieve median usdt/USD price."""
    mock_prices = [1.0001, 1.0002, 1.0003, 1.0004, 1.0005]
    mock_price_feed(usdt_usd_median_feed, mock_prices)
    v, _ = await usdt_usd_median_feed.source.fetch_new_datapoint()

    assert v is not None
    assert v > 0
    assert "sources used in aggregate: 5" in caplog.text.lower()
    print(f"usdt/usd Price: {v}")
    source_prices = usdt_usd_median_feed.source.latest[0]
    # Get list of data sources from sources dict
    source_prices = [source.latest[0] for source in usdt_usd_median_feed.source.sources if source.latest[0]]

    # Make sure error is less than decimal tolerance
    assert (v - statistics.median(source_prices)) < 10**-6
