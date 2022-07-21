"""
EUR/USD DataFeed Tests
"""
import pytest

from telliot_feeds.feeds.eur_usd_feed import eur_usd_median_feed


@pytest.mark.asyncio
async def test_fetch_price():
    """Fetch latest EUR/USD price"""
    (value, _) = await eur_usd_median_feed.source.fetch_new_datapoint()
    assert value > 0
    print(value)
