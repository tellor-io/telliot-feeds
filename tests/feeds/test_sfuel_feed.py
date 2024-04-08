import pytest

from telliot_feeds.feeds.sfuel_usd_feed import sfuel_usd_feed


@pytest.mark.asyncio
async def test_sfuel_usd_feed(caplog):
    """Retrieve median sFUEL/USD price."""
    v, _ = await sfuel_usd_feed.source.fetch_new_datapoint()

    assert v is not None
    assert v == 0

    print(f"sFUEL/USD Price: {v}")
