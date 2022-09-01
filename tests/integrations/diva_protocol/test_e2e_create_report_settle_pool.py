"""
Settle a derivative pool in DIVA Protocol after reporting the value of
it's reference asset and collateral token.

Call `setFinalReferenceValue` on the DivaOracleTellor contract.
Ensure it can't be called twice, or if there's no reported value for the pool,
or if it's too early for the pool to be settled."""
import os
import time

import pytest
from brownie import accounts
from brownie import DIVAProtocolMock
from brownie import DIVATellorOracleMock
from brownie import TellorPlayground
from telliot_core.apps.core import ChainedAccount
from telliot_core.apps.core import find_accounts
from telliot_core.apps.core import TelliotCore
from telliot_core.tellor.tellorflex.diva import DivaOracleTellorContract

from telliot_feeds.integrations.diva_protocol.report import DIVAProtocolReporter
from telliot_feeds.integrations.diva_protocol.utils import get_reported_pools
from tests.utils.utils import passing_bool_w_status
from utils import EXAMPLE_POOLS_FROM_SUBGRAPH

# from unittest import mock


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
def mock_playground():
    return accounts[0].deploy(TellorPlayground)


@pytest.fixture
def mock_middleware_contract(mock_playground):
    return accounts[0].deploy(DIVATellorOracleMock, 0, mock_playground.address)


@pytest.mark.asyncio
async def test_create_report_settle_pool(
    goerli_test_cfg,
    mock_playground,
    mock_autopay_contract,
    mock_token_contract,
    mock_diva_contract,
    mock_middleware_contract,
    monkeypatch,
):
    """
    Test settling a derivative pool in DIVA Protocol after reporting the value of
    it's reference asset and collateral token.
    """
    async with TelliotCore(config=goerli_test_cfg) as core:
        past_expired = int(time.time()) - 1
        assert mock_middleware_contract.updateMinPeriodUndisputed.call(1, {"from": accounts[0]}) == 1

        # mock default_homedir to be current directory
        monkeypatch.setattr("telliot_feeds.integrations.diva_protocol.utils.default_homedir", lambda: os.getcwd())

        # check initial state of pools pickle file
        assert get_reported_pools() == {}

        # mock fetch pools from subgraph
        example_pools_updated = EXAMPLE_POOLS_FROM_SUBGRAPH
        example_pools_updated[0]["expiryTime"] = past_expired

        async def mock_fetch_pools(*args, **kwargs):
            return example_pools_updated

        # create pool in DIVA Protocol
        pool_id = int(example_pools_updated[0]["id"])
        _ = mock_diva_contract.addPool(
            pool_id,
            [
                example_pools_updated[0]["referenceAsset"],
                example_pools_updated[0]["expiryTime"],
                0,
                0,
                0,
                0,
                example_pools_updated[0]["collateralToken"]["id"],
                0,
                0,
                example_pools_updated[0]["collateralBalance"],
                "0x0000000000000000000000000000000000000000",
                "0x0000000000000000000000000000000000000000",
                0,
                0,
                0,
                0,
                0,
                mock_middleware_contract.address,
                0,
                0,
                0,
            ],
            {"from": accounts[0]},
        )
        # ensure pool is created
        params = mock_diva_contract.getPoolParameters.call(pool_id, {"from": accounts[0]})  # print("params", params)
        assert params[0] == example_pools_updated[0]["referenceAsset"]
        assert params[1] == past_expired
        assert params[17] == mock_middleware_contract.address
        # ensure statusFinalReferenceValue is not submitted (Open)
        assert params[13] == 0

        # instantiate reporter w/ mock contracts & data provider and any other params
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
            datafeed=None,
            transaction_type=0,
            wait_period=0,
            wait_before_settle=1,
        )
        r.ensure_staked = passing_bool_w_status
        r.fetch_unfiltered_pools = mock_fetch_pools
        r.middleware_contract = DivaOracleTellorContract(core.endpoint, account)
        r.middleware_contract.address = mock_middleware_contract.address
        r.middleware_contract.connect()

        await r.report(report_count=1)

        # check pool settled, status updated to Submitted
        assert mock_diva_contract.getPoolParameters.call(pool_id, {"from": accounts[0]})[13] == 1

        # check reported pools pickle file state updated
        assert get_reported_pools() == {}

        # run report again, check no new pools picked up, unable to report & settle
        await r.report(report_count=1)
        assert get_reported_pools() == {}

        # clean up temp pickle file
        adir = os.getcwd()
        _ = [os.remove(adir + "/" + f) for f in os.listdir(adir) if f.endswith(".pickle")]
