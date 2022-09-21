import pytest
import pytest_asyncio
from brownie import accounts
from brownie import TellorFlex360
from telliot_core.apps.core import TelliotCore
from telliot_feeds.queries.query_catalog import query_catalog
from telliot_feeds.reporters.tellorflex_360 import TellorFlex360Reporter


trb_id = query_catalog._entries["trb-usd-spot"].query.query_id
txn_kwargs = {"gas_limit": 3500000, "legacy_gas_price": 1}
account_fake = accounts.add("023861e2ceee1ea600e43cbd203e9e01ea2ed059ee3326155453a1ed3b1113a9")
@pytest.fixture(scope="function")
def tellorflex_360_contract(mock_token_contract):
    return account_fake.deploy(
        TellorFlex360,
        mock_token_contract.address,
        1,
        1,
        1,
        trb_id.hex(),
        )
@pytest_asyncio.fixture(scope="function")
async def reporter_360(
    mumbai_test_cfg, tellorflex_360_contract, mock_autopay_contract, mock_token_contract, multicall_contract
):
    async with TelliotCore(config=mumbai_test_cfg) as core:

        account = core.get_account()

        flex = core.get_tellorflex_contracts()
        flex.oracle.address = tellorflex_360_contract.address
        flex.oracle.abi = tellorflex_360_contract.abi
        flex.autopay.address = mock_autopay_contract.address
        flex.autopay.abi = mock_autopay_contract.abi
        flex.token.address = mock_token_contract.address

        flex.oracle.connect()
        flex.token.connect()
        flex.autopay.connect()
        flex = core.get_tellorflex_contracts()

        r = TellorFlex360Reporter(
            oracle=flex.oracle,
            token=flex.token,
            autopay=flex.autopay,
            endpoint=core.endpoint,
            account=account,
            chain_id=80001,
            transaction_type=0,
        )
        # mint token and send to reporter address
        mock_token_contract.mint(account.address, 1000e18)

        # send eth from brownie address to reporter address for txn fees
        accounts[1].transfer(account.address, "1 ether")
        # init governance address
        await flex.oracle.write("init", _governanceAddress=accounts[0].address, **txn_kwargs)

        return r

@pytest.mark.asyncio
async def test_report(reporter_360, caplog):
    """Test 360 reporter deposit and balance changes when stakeAmount changes"""
    r: TellorFlex360Reporter = reporter_360

    await r.report_once()
    assert r.staker_info.stake_balance == int(1e18)
    # report count before first submission
    assert r.staker_info.reports_count == 0

    # update stakeamount increase causes reporter to deposit more to keep reporting
    await r.oracle.write("updateStakeAmount", _amount=int(20e18), **txn_kwargs)
    stake_amount, status = await r.oracle.read("getStakeAmount")
    assert status.ok
    assert stake_amount == int(20e18)

    await r.report_once()
    # staker balance increased due to updateStakeAmount call
    assert r.staker_info.stake_balance == stake_amount
    assert "Currently in reporter lock. Time left: 11:59" in caplog.text #12hr
    # report count before second report
    assert r.staker_info.reports_count == 1
    # decrease stakeAmount should increase reporting frequency
    await r.oracle.write("updateStakeAmount", _amount=int(10e18), **txn_kwargs)
    stake_amount, status = await r.oracle.read("getStakeAmount")
    assert status.ok
    assert stake_amount == int(10e18)

    assert r.staker_info.stake_balance == int(20e18)
    
    await r.report_once()
    assert "Currently in reporter lock. Time left: 5:59" in caplog.text #6hr
