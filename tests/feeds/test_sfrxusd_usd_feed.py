import statistics

import pytest

from telliot_feeds.feeds.sfrxusd_usd_feed import sfrxusd_usd_median_feed


@pytest.mark.asyncio
async def test_sfrxusd_usd_median_feed(mock_price_feed, caplog):
    """Retrieve median SFRXUSD/USD price."""
    mock_prices = [1.50, 1.51, 1.52, 1.53]
    mock_price_feed(sfrxusd_usd_median_feed, mock_prices)
    v, _ = await sfrxusd_usd_median_feed.source.fetch_new_datapoint()

    assert v is not None
    assert v > 0
    assert "sources used in aggregate: 4" in caplog.text.lower()
    print(f"SFRXUSD/USD Price: {v}")

    # Get list of data sources from sources dict
    source_prices = [source.latest[0] for source in sfrxusd_usd_median_feed.source.sources]
    print(source_prices)

    # Make sure error is less than decimal tolerance
    assert (v - statistics.median(source_prices)) < 10**-6
