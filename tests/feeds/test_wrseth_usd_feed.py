from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest

from telliot_feeds.feeds.wrseth_usd_feed import wrseth_usd_feed


@pytest.mark.asyncio
async def test_wrseth_usd_feed(caplog, mock_price_feed):
    """Retrieve median WrsETH/USD price."""
    # Mock the blockchain call that gets the wrsETH ratio
    with patch("telliot_feeds.sources.wrseth_source.wrsETHSpotPriceService.get_wrseth_eth_ratio", return_value=1.05):
        # Mock the underlying price sources for rsETH
        # mock_prices = [3200.50, 3205.25, 3202.75, 3201.00]

        # Create a mock price aggregator for the internal sources
        with patch("telliot_feeds.sources.wrseth_source.PriceAggregator") as mock_aggregator:
            mock_aggregator_instance = mock_aggregator.return_value
            mock_aggregator_instance.fetch_new_datapoint = AsyncMock(return_value=(3202.125, None))

            v, _ = await wrseth_usd_feed.source.fetch_new_datapoint()

            assert v is not None
            assert v > 0
            # Expected price should be approximately 3202.125 * 1.05 = 3362.23
            expected_price = 3202.125 * 1.05
            assert abs(v - expected_price) < 1.0  # Allow small tolerance
            print(f"WrsETH/USD Price: {v}")
