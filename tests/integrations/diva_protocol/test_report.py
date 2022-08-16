"""Report values for construced DIVA Protocol queries.

Prevent early reporting of data for DIVA Protocol queries.
Ensure others haven't already reported data for the same query."""
import time

import pytest
from brownie import accounts
from brownie import DIVAProtocolMock
from telliot_core.apps.core import TelliotCore
from web3.datastructures import AttributeDict

from telliot_feeds.integrations.diva_protocol.feed import assemble_diva_datafeed
from telliot_feeds.reporters.tellorflex import TellorFlexReporter


@pytest.mark.asyncio
async def test_report():
    pass


@pytest.mark.asyncio
async def test_report_fail():
    pass


@pytest.fixture
def mock_diva_contract():
    return accounts[0].deploy(DIVAProtocolMock)


@pytest.mark.skip
@pytest.mark.asyncio
async def test_diva_protocol_reporter_submit_once(
    ropsten_test_cfg,
    mock_flex_contract,
    mock_autopay_contract,
    mock_token_contract,
    mock_diva_contract,
):
    """Test reporting DIVA Protocol pool response on mumbai."""
    async with TelliotCore(config=ropsten_test_cfg) as core:
        account = core.get_account()

        pool_id = 10

        diva_feed = await assemble_diva_datafeed(
            pool_id=pool_id,
            node=core.endpoint,
            account=account,
            diva_address=mock_diva_contract.address,
        )

        # Use current timestamp for pool expiry time
        new_expiry = mock_diva_contract.changePoolExpiry(pool_id, int(time.time() - 1234))
        print(f"new_expiry: {new_expiry}")

        flex = core.get_tellorflex_contracts()
        flex.oracle.address = mock_flex_contract.address
        flex.autopay.address = mock_autopay_contract.address
        flex.token.address = mock_token_contract.address
        flex.oracle.connect()
        flex.token.connect()
        flex.autopay.connect()
        # mint token and send to reporter address
        mock_token_contract.mint(account.address, 1000e18)
        # send eth from brownie address to reporter address for txn fees
        accounts[2].transfer(account.address, "1 ether")
        r = TellorFlexReporter(
            endpoint=core.endpoint,
            account=account,
            chain_id=80001,
            oracle=flex.oracle,
            token=flex.token,
            autopay=flex.autopay,
            transaction_type=0,
            datafeed=diva_feed,
            max_fee=100,
            expected_profit="YOLO",
        )
        ORACLE_ADDRESSES = {mock_flex_contract.address}
        tx_receipt, status = await r.report_once()
        # Reporter submitted
        if tx_receipt is not None and status.ok:
            assert isinstance(tx_receipt, AttributeDict)
            assert tx_receipt.to in ORACLE_ADDRESSES
        # Reporter did not submit
        else:
            assert not tx_receipt
            assert not status.ok
            assert (
                ("Currently in reporter lock." in status.error)
                or ("Current addess disputed" in status.error)
                or ("Unable to retrieve updated datafeed" in status.error)
            )
