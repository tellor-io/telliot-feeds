from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest

from telliot_feeds.feeds.reth_usd_feed import reth_usd_median_feed


@pytest.mark.asyncio
async def test_reth_usd_median_feed(caplog):
    """Retrieve fundamental RETH/USD price (ETH/USD median × rETH exchange rate)."""
    with patch("telliot_feeds.sources.reth_source.RethSpotPriceService.get_reth_eth_ratio", return_value=1.05):
        with patch(
            "telliot_feeds.sources.reth_source.eth_usd_median_feed.source.fetch_new_datapoint",
            new_callable=AsyncMock,
            return_value=(3202.125, None),
        ):
            v, _ = await reth_usd_median_feed.source.fetch_new_datapoint()

            assert v is not None
            assert v > 0
            expected_price = 3202.125 * 1.05
            assert abs(v - expected_price) < 1.0
            print(f"RETH/USD Price: {v}")
