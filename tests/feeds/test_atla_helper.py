import pytest

from telliot_feeds.feeds.atla_helper_feed import atla_helper_feed


@pytest.mark.asyncio
async def test_atla_helper_feed(caplog):
    """Retrieves $1 ATLA/USD price for telliot's internal functionality"""
    v, _ = await atla_helper_feed.source.fetch_new_datapoint()

    assert v == 1.00

    print(f"ATLA/USD Price: {v}")
