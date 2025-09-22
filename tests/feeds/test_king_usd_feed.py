import statistics

import pytest

from telliot_feeds.feeds.king_usd_feed import king_usd_median_feed


@pytest.mark.asyncio
async def test_king_usd_median_feed(mock_price_feed, caplog):
    """Retrieve median KING/USD price."""
    mock_prices = [1041.19, 1055.66]
    mock_price_feed(king_usd_median_feed, mock_prices)
    v, _ = await king_usd_median_feed.source.fetch_new_datapoint()

    assert v is not None
    assert v > 0
    assert "sources used in aggregate: 2" in caplog.text.lower()
    print(f"KING/USD Price: {v}")

    # Get list of data sources from sources dict
    source_prices = [source.latest[0] for source in king_usd_median_feed.source.sources]
    print(source_prices)

    # Make sure error is less than decimal tolerance
    assert (v - statistics.median(source_prices)) < 10**-6
