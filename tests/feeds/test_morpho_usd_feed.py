import statistics

import pytest

from telliot_feeds.feeds.morpho_usd_feed import morpho_usd_median_feed


@pytest.mark.asyncio
async def test_morpho_usd_median_feed(mock_price_feed, caplog):
    """Retrieve median MORPHO/USD price."""
    mock_prices = [2.422, 2.428, 2.430]
    mock_price_feed(morpho_usd_median_feed, mock_prices)
    v, _ = await morpho_usd_median_feed.source.fetch_new_datapoint()

    assert v is not None
    assert v > 0
    assert "sources used in aggregate: 3" in caplog.text.lower()
    print(f"MORPHO/USD Price: {v}")

    # Get list of data sources from sources dict
    source_prices = [source.latest[0] for source in morpho_usd_median_feed.source.sources]
    print(source_prices)

    # Make sure error is less than decimal tolerance
    assert (v - statistics.median(source_prices)) < 10**-6
