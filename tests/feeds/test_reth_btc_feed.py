import statistics

import pytest

from telliot_feeds.feeds.reth_btc_feed import reth_btc_median_feed


@pytest.mark.asyncio
async def test_reth_btc_median_feed(caplog, mock_price_feed):
    """Retrieve median RETH/BTC price."""
    mock_prices = [1200.50, 1205.25]
    mock_price_feed(reth_btc_median_feed, mock_prices)
    v, _ = await reth_btc_median_feed.source.fetch_new_datapoint()

    assert v is not None
    assert v > 0
    assert "sources used in aggregate: 2" in caplog.text.lower()
    print(f"RETH/BTC Price: {v}")

    # Get list of data sources from sources dict
    source_prices = [source.latest[0] for source in reth_btc_median_feed.source.sources if source.latest[0]]

    # Make sure error is less than decimal tolerance
    assert (v - statistics.median(source_prices)) < 10**-6
