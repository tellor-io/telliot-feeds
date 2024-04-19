import pytest

from telliot_feeds.feeds.leth_usd_feed import leth_usd_feed


@pytest.mark.asyncio
async def test_leth_usd_feed(caplog):
    """Retrieve median ETH/USD price converted to LETH/USD by ratio"""
    v, _ = await leth_usd_feed.source.fetch_new_datapoint()

    assert v is not None
    assert v > 0
    assert "sources used in aggregate: 4" in caplog.text.lower()
    print(f"sfrax/usd Price: {v}")

    # Get list of data sources from sources dict
    # source_prices = [source.latest[0] for source in sfrax_usd_median_feed.source.sources if source.latest[0]]

    # Make sure error is less than decimal tolerance
    # assert (v - statistics.median(source_prices)) < 10**-6
