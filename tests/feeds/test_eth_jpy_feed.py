import statistics

import pytest

from telliot_feeds.feeds.eth_jpy_feed import eth_jpy_median_feed


@pytest.mark.asyncio
async def test_AssetPriceFeed():
    """Retrieve median ETH/JPY price."""
    v, _ = await eth_jpy_median_feed.source.fetch_new_datapoint()

    assert v is not None
    assert v > 0
    print(f"ETH/JPY Price: {v}")

    # Get list of data sources from sources dict
    source_prices = [source.latest[0] for source in eth_jpy_median_feed.source.sources]
    print(source_prices)

    # Make sure error is less than decimal tolerance
    assert (v - statistics.median(source_prices)) < 10**-6
