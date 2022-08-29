"""Report values for construced DIVA Protocol queries.

Prevent early reporting of data for DIVA Protocol queries.
Ensure others haven't already reported data for the same query."""
import time

import pytest
from brownie import accounts
from brownie import DIVAProtocolMock
from brownie import DIVATellorOracleMock
from telliot_core.apps.core import TelliotCore
from telliot_core.tellor.tellorflex.diva import DivaOracleTellorContract
from web3.datastructures import AttributeDict

from telliot_feeds.integrations.diva_protocol.feed import assemble_diva_datafeed
from telliot_feeds.integrations.diva_protocol.report import DIVAProtocolReporter


@pytest.fixture
def mock_diva_contract():
    return accounts[0].deploy(DIVAProtocolMock)


@pytest.fixture
def mock_middleware_contract():
    return accounts[0].deploy(DIVATellorOracleMock)


@pytest.mark.asyncio
async def test_report(
    goerli_test_cfg,
    mock_flex_contract,
    mock_autopay_contract,
    mock_token_contract,
    mock_diva_contract,
    mock_middleware_contract,
):
    """Test reporting DIVA Protocol pool response on mumbai."""
    async with TelliotCore(config=goerli_test_cfg) as core:
        account = core.get_account()

        chain_id = 5
        pool_id = 1234

        diva_feed = await assemble_diva_datafeed(
            node=core.endpoint,
            account=account,
            pool_id=pool_id,
            diva_address=mock_diva_contract.address,
            chaind_id=chain_id,
        )

        # Use current timestamp minus 30 sec for pool expiry time
        _ = mock_diva_contract.changePoolExpiry(pool_id, int(time.time() - 30))

        flex = core.get_tellorflex_contracts()
        flex.oracle.address = mock_flex_contract.address
        flex.autopay.address = mock_autopay_contract.address
        flex.token.address = mock_token_contract.address
        flex.oracle.connect()
        flex.token.connect()
        flex.autopay.connect()
        mock_token_contract.mint(account.address, 1000e18)
        accounts[2].transfer(account.address, "1 ether")

        r = DIVAProtocolReporter(
            endpoint=core.endpoint,
            account=account,
            chain_id=chain_id,
            oracle=flex.oracle,
            token=flex.token,
            autopay=flex.autopay,
            datafeed=diva_feed,
            expected_profit="YOLO",
        )
        r.middleware_contract = DivaOracleTellorContract(core.endpoint, account)
        r.middleware_contract.address = mock_middleware_contract.address
        r.middleware_contract.connect()
        tx_receipt, status = await r.report_once()

        assert status.ok
        assert isinstance(tx_receipt, AttributeDict)
        assert tx_receipt.to == mock_flex_contract.address

        # Check that the report was recorded in the mock contract


@pytest.mark.asyncio
async def test_report_twice_fail():
    # ensure can't report same pool twice
    pass


@pytest.mark.asyncio
async def test_report_early_fail():
    # ensure can't report before expiry time
    pass
