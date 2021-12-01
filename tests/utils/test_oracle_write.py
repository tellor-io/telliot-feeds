import pytest
from telliot_core.utils.response import ResponseStatus
from web3.datastructures import AttributeDict

from telliot_feed_examples.feeds.eth_usd_feed import eth_usd_median_feed
from telliot_feed_examples.utils.oracle_write import tip_query


@pytest.mark.asyncio
async def test_tip_query(oracle):
    """Test tipping ETH/USD price."""
    tip = int(0.00001 * 1e18)
    tx_receipt, status = await tip_query(
        oracle=oracle,
        datafeed=eth_usd_median_feed,
        tip=tip,
    )

    assert isinstance(tx_receipt, AttributeDict)
    assert isinstance(status, ResponseStatus)
    assert status.ok
