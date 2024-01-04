import statistics

import pytest

from telliot_feeds.feeds.ogv_eth_feed import ogv_eth_median_feed


@pytest.mark.asyncio
async def test_ogv_eth_median_feed(caplog):
    """Retrieve median ogv/ETH price."""
    v, _ = await ogv_eth_median_feed.source.fetch_new_datapoint()

    assert v is not None
    assert v > 0
    assert "sources used in aggregate: 2" in caplog.text.lower()
    print(f"ogv/eth Price: {v}")

    # Get list of data sources from sources dict
    source_prices = [source.latest[0] for source in ogv_eth_median_feed.source.sources if source.latest[0]]

    # Make sure error is less than decimal tolerance
    assert (v - statistics.median(source_prices)) < 10**-6
