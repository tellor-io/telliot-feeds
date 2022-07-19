import pytest
from brownie import accounts
from telliot_core.apps.core import TelliotCore
from telliot_core.utils.response import ResponseStatus
from web3.datastructures import AttributeDict

from telliot_feeds.feeds.eth_usd_feed import eth_usd_median_feed
from telliot_feeds.utils.oracle_write import tip_query


@pytest.mark.skip("Disabled until we need this functionality")
@pytest.mark.asyncio
async def test_tip_query(rinkeby_test_cfg):
    """Test tipping ETH/USD price."""

    async with TelliotCore(config=rinkeby_test_cfg) as core:
        accounts[1].transfer(core.get_account().address, "1 ether")
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
