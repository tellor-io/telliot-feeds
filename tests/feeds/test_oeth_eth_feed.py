import pytest

from telliot_feeds.feeds.oeth_eth_feed import oeth_eth_feed


@pytest.mark.asyncio
async def test_oeth_eth_feed(caplog):
    """Retrieve median OETH/ETH price."""
    v, _ = await oeth_eth_feed.source.fetch_new_datapoint()

    assert v is not None
    assert v > 0
    print(f"OETH/ETH Price: {v}")
