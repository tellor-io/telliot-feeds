from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest

from telliot_feeds.feeds.sfrax_usd_feed import sfrax_usd_feed


@pytest.mark.asyncio
async def test_sfrax_usd_feed(caplog):
    """Retrieve median sFRAX/USD price converted by ratio from sFRAX contract"""
    # Mock the blockchain call that gets the sFRAX/USD ratio
    with patch(
        "telliot_feeds.sources.sfrax_source.sFRAXSpotPriceService.get_sfrax_usd_ratio", return_value=1.08
    ):
        # Mock the PriceAggregator that fetches FRAX prices from multiple sources
        with patch("telliot_feeds.sources.sfrax_source.PriceAggregator") as mock_aggregator:
            mock_aggregator_instance = mock_aggregator.return_value
            mock_aggregator_instance.fetch_new_datapoint = AsyncMock(return_value=(1.0, None))

            v, _ = await sfrax_usd_feed.source.fetch_new_datapoint()

            assert v is not None
            assert v > 0
            # Expected price should be approximately 1.0 * 1.08 = 1.08
            expected_price = 1.0 * 1.08
            assert abs(v - expected_price) < 0.01
            print(f"sFRAX/USD Price: {v}")
