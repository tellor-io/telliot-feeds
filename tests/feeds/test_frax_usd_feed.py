import statistics

import pytest

from telliot_feeds.feeds.frax_usd_feed import frax_usd_median_feed


@pytest.mark.asyncio
async def test_frax_usd_feed(mock_price_feed, caplog):
    """Retrieve median FRAX/USD price converted to wUSDM by ratio"""
    mock_prices = [1200.50, 1205.25, 1202.75, 1200.50]
    mock_price_feed(frax_usd_median_feed, mock_prices)
    v, _ = await frax_usd_median_feed.source.fetch_new_datapoint()

    assert v is not None
    assert v > 0
    assert "sources used in aggregate: 4" in caplog.text.lower()
    print(f"frax/usd Price: {v}")

    # Get list of data sources from sources dict
    source_prices = [source.latest[0] for source in frax_usd_median_feed.source.sources if source.latest[0]]

    # Make sure error is less than decimal tolerance
    assert (v - statistics.median(source_prices)) < 10**-6
