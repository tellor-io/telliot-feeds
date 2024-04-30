import pytest

from telliot_feeds.feeds.sfuel_helper_feed import sfuel_helper_feed


@pytest.mark.asyncio
async def test_sfuel_helper_feed(caplog):
    """Retrieves $1 sFUEL/USD price for telliot's internal functionality"""
    v, _ = await sfuel_helper_feed.source.fetch_new_datapoint()

    assert v == 1.00

    print(f"sFUEL/USD Price: {v}")
