import statistics

import pytest

from telliot_feeds.feeds.rseth_usd_feed import rseth_usd_median_feed


@pytest.mark.asyncio
async def test_rseth_usd_median_feed(caplog, mock_price_feed):
    """Retrieve median rsETH/USD price."""
    mock_prices = [1200.50, 1205.25, 1202.75, 1203.00]
    mock_price_feed(rseth_usd_median_feed, mock_prices)
    v, _ = await rseth_usd_median_feed.source.fetch_new_datapoint()

    assert v is not None
    assert v > 0
    assert "sources used in aggregate: 4" in caplog.text.lower()
    print(f"rsETH/USD Price: {v}")
    # Get list of data sources from sources dict
    source_prices = rseth_usd_median_feed.source.latest[0]

    # Make sure error is less than decimal tolerance
    assert (v - statistics.median([source_prices])) < 10**-6
