import statistics

import pytest

from telliot_feed_examples.feeds.eth_usd_feed import eth_usd_median_feed


@pytest.mark.asyncio
async def test_AssetPriceFeed():
    """Retrieve median ETH/USD price."""
    v, _ = await eth_usd_median_feed.source.fetch_new_datapoint()

    assert v is not None
    assert v > 0
    print(f"ETH/USD Price: {v}")

    # Get list of data sources from sources dict
    source_prices = [source.latest[0] for source in eth_usd_median_feed.source.sources]

    # Make sure error is less than decimal tolerance
    assert (v - statistics.median(source_prices)) < 10 ** -6
