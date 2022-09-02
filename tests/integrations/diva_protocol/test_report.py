"""Report values for construced DIVA Protocol queries.

Prevent early reporting of data for DIVA Protocol queries.
Ensure others haven't already reported data for the same query."""
import time

import pytest
from brownie import accounts
from brownie import DIVAProtocolMock
from brownie import DIVATellorOracleMock
from brownie import TellorPlayground
from telliot_core.apps.core import ChainedAccount
from telliot_core.apps.core import find_accounts
from telliot_core.apps.core import TelliotCore
from web3.datastructures import AttributeDict

from telliot_feeds.integrations.diva_protocol.contract import DivaOracleTellorContract
from telliot_feeds.integrations.diva_protocol.feed import assemble_diva_datafeed
from telliot_feeds.integrations.diva_protocol.pool import DivaPool
from telliot_feeds.integrations.diva_protocol.report import DIVAProtocolReporter
from tests.utils.utils import passing_bool_w_status


chain_id = 5
_ = accounts.add("023861e2ceee1ea600e43cbd203e9e01ea2ed059ee3326155453a1ed3b1113a9")
try:
    account = find_accounts(name="fake_goerli_test_acct", chain_id=chain_id)[0]
except IndexError:
    account = ChainedAccount.add(
        name="fake_goerli_test_acct",
        chains=chain_id,
        key="023861e2ceee1ea600e43cbd203e9e01ea2ed059ee3326155453a1ed3b1113a9",
        password="",
    )


@pytest.fixture
def mock_diva_contract():
    return accounts[0].deploy(DIVAProtocolMock)


@pytest.fixture
def mock_middleware_contract(mock_playground):
    return accounts[0].deploy(DIVATellorOracleMock, 0, mock_playground.address)


@pytest.fixture
def mock_playground():
    return accounts[0].deploy(TellorPlayground)


@pytest.mark.skip("kind of redundant test since done in e2e one")
@pytest.mark.asyncio
async def test_report(
    goerli_test_cfg,
    mock_playground,
    mock_autopay_contract,
    mock_token_contract,
    mock_diva_contract,
    mock_middleware_contract,
):
    """Test reporting DIVA Protocol pool response on mumbai."""
    async with TelliotCore(config=goerli_test_cfg) as core:

        past_expiry = int(time.time()) - 1
        pool_id = 1234
        fake_pool = DivaPool(
            pool_id=pool_id,
            reference_asset="ETH/USD",
            collateral_token_address="0x1234",
            collateral_token_symbol="dUSD",
            collateral_balance=100,
            expiry_time=past_expiry,
        )
        diva_feed = assemble_diva_datafeed(pool=fake_pool)
        _ = mock_diva_contract.changePoolExpiry(pool_id, past_expiry)

        timestamp = mock_playground.getNewValueCountbyQueryId(diva_feed.query.query_id)
        assert timestamp == 0

        flex = core.get_tellorflex_contracts()
        flex.oracle.address = mock_playground.address
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
            expected_profit="YOLO",
            datafeed=diva_feed,
            transaction_type=0,
        )
        r.ensure_staked = passing_bool_w_status
        r.middleware_contract = DivaOracleTellorContract(core.endpoint, account)
        r.middleware_contract.address = mock_middleware_contract.address
        r.middleware_contract.connect()
        tx_receipt, status = await r.report_once()

        assert status.ok
        assert isinstance(tx_receipt, AttributeDict)
        assert tx_receipt.to == mock_playground.address

        # Check that the report was recorded in the mock contract
        idx = mock_playground.getNewValueCountbyQueryId(diva_feed.query.query_id)
        assert idx == 1

        timestamp = mock_playground.getTimestampbyQueryIdandIndex(diva_feed.query.query_id, 0)
        assert timestamp > past_expiry

        val = mock_playground.retrieveData(diva_feed.query.query_id, timestamp)
        ref_asset_price, dusd_price = diva_feed.query.value_type.decode(val)
        assert ref_asset_price > 0
        assert dusd_price == 1
