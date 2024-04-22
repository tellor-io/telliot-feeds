import pytest

from telliot_feeds.feeds.leth_usd_feed import leth_usd_feed


@pytest.mark.asyncio
async def test_leth_usd_feed(caplog):
    """Retrieve median ETH/USD price converted to LETH/USD by ratio"""
    v, _ = await leth_usd_feed.source.fetch_new_datapoint()

    assert v is not None
    assert v > 0
    # check contract response
    assert "total pooled tokens" in caplog.text.lower()
    assert "total supply" in caplog.text.lower()
    # check 4 sources for ETH/USD price:
    assert "sources used in aggregate: 4" in caplog.text.lower()
    print(f"LETH/USD Price: {v}")
