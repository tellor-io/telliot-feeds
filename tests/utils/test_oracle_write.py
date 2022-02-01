import pytest
from telliot_core.apps.core import TelliotCore
from telliot_core.utils.response import ResponseStatus
from web3.datastructures import AttributeDict

from telliot_feed_examples.feeds.eth_usd_feed import eth_usd_median_feed
from telliot_feed_examples.utils.oracle_write import tip_query


@pytest.mark.skip("Get rid of passwd ask for tests")
@pytest.mark.asyncio
async def test_tip_query(rinkeby_cfg):
    """Test tipping ETH/USD price."""

    async with TelliotCore(config=rinkeby_cfg) as core:
        tellorx = core.get_tellorx_contracts()
        tip = int(0.0001 * 1e18)
        tx_receipt, status = await tip_query(
            oracle=tellorx.oracle,
            datafeed=eth_usd_median_feed,
            tip=tip,
        )

        assert isinstance(tx_receipt, AttributeDict)
        assert isinstance(status, ResponseStatus)
        assert status.ok
