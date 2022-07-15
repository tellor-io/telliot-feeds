import pytest
from brownie import accounts
from telliot_core.apps.core import TelliotCore
from web3.datastructures import AttributeDict

from telliot_feeds.feeds.uspce_feed import uspce_feed
from telliot_feeds.reporters.interval import IntervalReporter
from telliot_feeds.sources import uspce


@pytest.mark.asyncio
async def test_uspce_interval_reporter_submit_once(
    rinkeby_test_cfg, tellorx_master_mock_contract, tellorx_oracle_mock_contract
):
    """test report of uspce manual price"""
    # Override Python built-in input method
    uspce.input = lambda: "123.456"

    async with TelliotCore(config=rinkeby_test_cfg) as core:

        account = core.get_account()
        tellorx = core.get_tellorx_contracts()
        tellorx.master.address = tellorx_master_mock_contract.address
        tellorx.oracle.address = tellorx_oracle_mock_contract.address
        tellorx.master.connect()
        tellorx.oracle.connect()
        r = IntervalReporter(
            endpoint=core.config.get_endpoint(),
            account=account,
            master=tellorx.master,
            oracle=tellorx.oracle,
            datafeed=uspce_feed,
            expected_profit="YOLO",
            transaction_type=0,
            gas_limit=400000,
            max_fee=None,
            priority_fee=None,
            legacy_gas_price=None,
            gas_price_speed="safeLow",
            chain_id=core.config.main.chain_id,
        )

        # send eth from brownie address to reporter address for txn fees
        accounts[0].transfer(account.address, "1 ether")

        EXPECTED_ERRORS = {
            "Current addess disputed. Switch address to continue reporting.",
            "Current address is locked in dispute or for withdrawal.",
            "Current address is in reporter lock.",
            "Estimated profitability below threshold.",
            "Estimated gas price is above maximum gas price.",
            "Unable to retrieve updated datafeed value.",
            "Unable to fetch ETH/USD price for profit calculation",
        }

        ORACLE_ADDRESSES = {r.oracle.address}

        tx_receipt, status = await r.report_once()

        # Reporter submitted
        if tx_receipt is not None and status.ok:
            assert isinstance(tx_receipt, AttributeDict)
            assert tx_receipt.to in ORACLE_ADDRESSES
        # Reporter did not submit
        else:
            assert not tx_receipt
            assert not status.ok
            assert status.error in EXPECTED_ERRORS
