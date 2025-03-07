import statistics

import pytest

from telliot_feeds.sources.gyd_source import gydSpotPriceService
from telliot_feeds.feeds.gyd_usd_feed import gyd_usd_median_feed


@pytest.mark.asyncio
async def test_gyd_usd_median_feed(caplog):
    """Retrieve median GYD/USD price."""
    v, _ = await gyd_usd_median_feed.source.fetch_new_datapoint()

    assert v is not None
    assert v > 0
    assert "sources used in aggregate: 2" in caplog.text.lower()
    print(f"GYD/USD Price: {v}")

    # Get list of data sources from sources dict
    source_prices = [source.latest[0] for source in gyd_usd_median_feed.source.sources if source.latest[0]]

    # Make sure error is less than decimal tolerance
    assert (v - statistics.median(source_prices)) < 10**-6

async def test_0_response_from_balancer(caplog):
    """Test that the GYD/USD feed returns None if the Balancer pools return 0"""
    # Create a test-only version of the class that doesn't get registered
    class TestGydSource:
        asset: str = "gyd"
        currency: str = "usd"
        service: gydSpotPriceService = field(default_factory=gydSpotPriceService, init=False)

    source = TestGydSource(asset="gyd", currency="usd")
    v, _ = await source.fetch_new_datapoint()
    assert v is None
    assert "Balancer pool price is 0, returning None" in caplog.text.lower()
