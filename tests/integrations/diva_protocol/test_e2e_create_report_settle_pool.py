"""
Settle a derivative pool in DIVA Protocol after reporting the value of
it's reference asset and collateral token.

Call `setFinalReferenceValue` on the DivaOracleTellor contract.
Ensure it can't be called twice, or if there's no reported value for the pool,
or if it's too early for the pool to be settled."""
import os
import time
from unittest import mock

import pytest
from brownie import accounts
from brownie import DIVAProtocolMock
from brownie import DIVATellorOracleMock
from brownie import TellorPlayground
from telliot_core.apps.core import ChainedAccount
from telliot_core.apps.core import find_accounts
from telliot_core.apps.core import TelliotCore

from telliot_feeds.integrations.diva_protocol.utils import get_reported_pools


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
def mock_middleware_contract():
    return accounts[0].deploy(DIVATellorOracleMock, 0)


@pytest.fixture
def mock_playground():
    return accounts[0].deploy(TellorPlayground)


@pytest.mark.asyncio
async def test_create_report_settle_pool(
    goerli_test_cfg,
    mock_playground,
    mock_autopay_contract,
    mock_token_contract,
    mock_diva_contract,
    mock_middleware_contract,
):
    """
    Test settling a derivative pool in DIVA Protocol after reporting the value of
    it's reference asset and collateral token.
    """
    async with TelliotCore(config=goerli_test_cfg) as core:
        _ = core
        pool_id = 10
        past_expired = int(time.time()) - 1
        # update values of fake pool
        assert mock_diva_contract.changePoolExpiry.call(pool_id, past_expired, {"from": accounts[0]}) == past_expired
        assert (
            mock_diva_contract.changePoolDataProvider.call(
                pool_id, mock_middleware_contract.address, {"from": accounts[0]}
            )
            == mock_middleware_contract.address
        )
        assert mock_middleware_contract.updateMinPeriodUndisputed.call(1, {"from": accounts[0]}) == 1

        # mock default_homedir to be current directory
        def mock_default_homedir():
            return os.getcwd()

        with mock.patch("telliot_feeds.integrations.diva_protocol.utils.default_homedir", mock_default_homedir):
            # instantiate reporter w/ mock contracts & data provider and any other params

            # check initial state of pools pickle file
            assert get_reported_pools() == {}

            # mock fetch pools from subgraph
            # run report for diva reporter, mock sleep to stop early

            # check value reported to flex contract
            # check pool info updated in pickle file
            # check pool settled in mock contract

            # run report again, check no new pools picked up, unable to report & settle

            # clean up temp pickle file
            adir = os.getcwd()
            _ = [os.remove(adir + "/" + f) for f in os.listdir(adir) if f.endswith(".pickle")]
