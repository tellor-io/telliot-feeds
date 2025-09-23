import statistics

import pytest

from telliot_feeds.feeds.fbtc_usd_feed import fbtc_usd_median_feed


@pytest.mark.asyncio
async def test_fbtc_usd_median_feed(mock_price_feed, caplog):
    """Retrieve median FBTC/USD price."""
    mock_prices = [95000.50, 95001.25]
    mock_price_feed(fbtc_usd_median_feed, mock_prices)
    v, _ = await fbtc_usd_median_feed.source.fetch_new_datapoint()

    assert v is not None
    assert v > 0
    assert "sources used in aggregate: 2" in caplog.text.lower()
    print(f"FBTC/USD Price: {v}")

    # Get list of data sources from sources dict
    source_prices = [source.latest[0] for source in fbtc_usd_median_feed.source.sources]
    print(source_prices)

    # Make sure error is less than decimal tolerance
    assert (v - statistics.median(source_prices)) < 10**-6
