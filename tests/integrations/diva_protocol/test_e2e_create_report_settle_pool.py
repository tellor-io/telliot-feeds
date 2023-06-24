"""
Settle a derivative pool in DIVA Protocol after reporting the value of
it's reference asset and collateral token.

Call `setFinalReferenceValue` on the DivaOracleTellor contract.
Ensure it can't be called twice, or if there's no reported value for the pool,
or if it's too early for the pool to be settled."""
import json
import os
import pickle
import time

import pytest
from brownie import accounts
from brownie import DIVAProtocolMock
from brownie import DIVATellorOracleMock
from brownie import TellorPlayground
from telliot_core.apps.core import ChainedAccount
from telliot_core.apps.core import find_accounts
from telliot_core.apps.core import TelliotCore
from telliot_core.utils.response import ResponseStatus

from telliot_feeds.integrations.diva_protocol.contract import DivaOracleTellorContract
from telliot_feeds.integrations.diva_protocol.report import DIVAProtocolReporter
from telliot_feeds.integrations.diva_protocol.utils import get_reported_pools
from tests.utils.utils import passing_bool_w_status
from utils import EXAMPLE_POOLS_FROM_SUBGRAPH

# from unittest import mock


CHAIN_ID = 5
_ = accounts.add("023861e2ceee1ea600e43cbd203e9e01ea2ed059ee3326155453a1ed3b1113a9")
try:
    account = find_accounts(name="fake_goerli_test_acct", chain_id=CHAIN_ID)[0]
except IndexError:
    account = ChainedAccount.add(
        name="fake_goerli_test_acct",
        chains=CHAIN_ID,
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
        past_expired = int(time.time()) - 86400  # 1 day ago
        assert (
            mock_middleware_contract.updateMinPeriodUndisputed.call(1, {"from": accounts[0]}) == 1
        ), "updateMinPeriodUndisputed failed"

        # mock default_homedir to be current directory
        monkeypatch.setattr("telliot_feeds.integrations.diva_protocol.utils.default_homedir", lambda: os.getcwd())

        if get_reported_pools() != {}:
            os.remove(os.getcwd() + "/" + "reported_pools.pickle")
        assert get_reported_pools() == {}, "reported pools pickle file not empty before test"

        # mock fetch pools from subgraph
        example_pools_updated = EXAMPLE_POOLS_FROM_SUBGRAPH
        example_pools_updated[0]["expiryTime"] = past_expired

        async def mock_fetch_pools(*args, **kwargs):
            return example_pools_updated[:1]

        async def mock_set_final_ref_value(*args, **kwargs):
            return ResponseStatus()

        # create pool in DIVA Protocol
        pool_id = example_pools_updated[0]["id"]
        print("pool_id", pool_id)
        _ = mock_diva_contract.addPool(
            pool_id,
            [
                0,  # example_pools_updated[0]["floor"],
                0,  # example_pools_updated[0]["inflection"],
                0,  # example_pools_updated[0]["cap"],
                0,  # example_pools_updated[0]["gradient"],
                example_pools_updated[0]["collateralBalance"],
                0,  # example_pools_updated[0]["finalReferenceValue"],
                0,  # example_pools_updated[0]["capacity"],
                0,  # example_pools_updated[0]["statusTimestamp"],
                "0x0000000000000000000000000000000000000000",  # example_pools_updated[0]["shortToken"],
                0,  # example_pools_updated[0]["payoutShort"],
                "0x0000000000000000000000000000000000000000",  # example_pools_updated[0]["longToken"],
                0,  # example_pools_updated[0]["payoutLong"],
                example_pools_updated[0]["collateralToken"]["id"],
                example_pools_updated[0]["expiryTime"],
                mock_middleware_contract.address,  # example_pools_updated[0]["dataProvider"],
                0,  # example_pools_updated[0]["protocolFee"],
                0,  # example_pools_updated[0]["settlementFee"],
                0,  # example_pools_updated[0]["statusFinalReferenceValue"],
                example_pools_updated[0]["referenceAsset"],
            ],
            {"from": accounts[0]},
        )
        # ensure pool is created
        params = mock_diva_contract.getPoolParameters.call(pool_id, {"from": accounts[0]})  # print("params", params)
        assert params[18] == example_pools_updated[0]["referenceAsset"], "reference asset is not correct"
        assert params[13] == past_expired, "expiryTime is not past_expired"
        assert params[14] == mock_middleware_contract.address, "incorrect data provider"
        # ensure statusFinalReferenceValue is not submitted (Open)
        assert params[17] == 0, "statusFinalReferenceValue status should be (Open)"

        # instantiate reporter w/ mock contracts & data provider and any other params
        flex = core.get_tellorflex_contracts()
        flex.oracle.address = mock_playground.address
        flex.autopay.address = mock_autopay_contract.address
        flex.token.address = mock_token_contract.address
        flex.oracle.connect()
        flex.token.connect()
        flex.autopay.connect()
        mock_token_contract.faucet(account.address)
        accounts[2].transfer(account.address, "1 ether")

        # before attempting to settle pools,
        # update the reported timestamp so it's 30 seconds ago, so it's ready to settle
        original_settle_pools = DIVAProtocolReporter.settle_pools

        def mock_settle_pools(self):
            reported_pools = get_reported_pools()
            reported_pools[pool_id][0] = int(time.time()) - 90
            pickle.dump(reported_pools, open(os.getcwd() + "/" + "reported_pools.pickle", "wb"))
            print("mock_settle_pools called")
            return original_settle_pools(self)

        monkeypatch.setattr(DIVAProtocolReporter, "settle_pools", mock_settle_pools)

        r = DIVAProtocolReporter(
            endpoint=core.endpoint,
            account=account,
            chain_id=CHAIN_ID,
            oracle=flex.oracle,
            token=flex.token,
            autopay=flex.autopay,
            expected_profit="YOLO",
            datafeed=None,
            transaction_type=0,
            wait_period=0,
            wait_before_settle=1,
            min_native_token_balance=0,
        )

        async def mock_check_reporter_lock():
            return ResponseStatus()

        r.check_reporter_lock = mock_check_reporter_lock
        r.ensure_staked = passing_bool_w_status
        r.fetch_unfiltered_pools = mock_fetch_pools
        r.set_final_ref_value = mock_set_final_ref_value
        r.middleware_contract = DivaOracleTellorContract(core.endpoint, account)
        r.middleware_contract.address = mock_middleware_contract.address
        r.middleware_contract.connect()

        await r.report(report_count=1)

        # check reported pools pickle file state updated
        updated_pools_pkl_file = get_reported_pools()
        print("updated_pools_pkl_file", json.dumps(updated_pools_pkl_file, indent=4))
        assert pool_id in updated_pools_pkl_file, "pool not in reported pools pickle file"
        assert "settled" in updated_pools_pkl_file[pool_id], "pool not marked as settled"
        assert int(time.time()) - 90 - updated_pools_pkl_file[pool_id][0] < 3, "reported time is off"

        print("Starting second report/settle attempt")
        # run report again, check no new pools picked up, does not report & settle
        r.datafeed = None
        await r.report(report_count=1)
        assert len(get_reported_pools()) == 1, "reported pools pickle file state incorrect after second report"
        assert pool_id in get_reported_pools(), "wrong pool in reported pools pickle file"

        # clean up temp pickle file
        adir = os.getcwd()
        _ = [os.remove(adir + "/" + f) for f in os.listdir(adir) if f.endswith(".pickle")]
