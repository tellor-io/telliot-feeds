import pytest
import pytest_asyncio
from brownie import accounts
from telliot_core.apps.core import TelliotCore

from telliot_feeds.reporters.rewards.time_based_rewards import get_time_based_rewards
from telliot_feeds.reporters.tellor_360 import Tellor360Reporter


txn_kwargs = {"gas_limit": 3500000, "legacy_gas_price": 1}
CHAIN_ID = 80001


@pytest_asyncio.fixture(scope="function")
async def tellor_360(mumbai_test_cfg, tellorflex_360_contract, mock_autopay_contract, mock_token_contract):
    async with TelliotCore(config=mumbai_test_cfg) as core:

        account = core.get_account()

        tellor360 = core.get_tellor360_contracts()
        tellor360.oracle.address = tellorflex_360_contract.address
        tellor360.oracle.abi = tellorflex_360_contract.abi
        tellor360.autopay.address = mock_autopay_contract.address
        tellor360.autopay.abi = mock_autopay_contract.abi
        tellor360.token.address = mock_token_contract.address

        tellor360.oracle.connect()
        tellor360.token.connect()
        tellor360.autopay.connect()

        # mint token and send to reporter address
        mock_token_contract.mint(account.address, 100000e18)

        # send eth from brownie address to reporter address for txn fees
        accounts[1].transfer(account.address, "1 ether")

        # init governance address
        await tellor360.oracle.write("init", _governanceAddress=accounts[0].address, **txn_kwargs)

        return tellor360, account


@pytest.mark.asyncio
async def test_report(tellor_360, caplog):
    """Test 360 reporter deposit and balance changes when stakeAmount changes"""
    contracts, account = tellor_360

    r = Tellor360Reporter(
        oracle=contracts.oracle,
        token=contracts.token,
        autopay=contracts.autopay,
        endpoint=contracts.oracle.node,
        account=account,
        chain_id=CHAIN_ID,
        transaction_type=0,
    )

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
    assert "Currently in reporter lock. Time left: 11:59" in caplog.text  # 12hr
    # report count before second report
    assert r.staker_info.reports_count == 1
    # decrease stakeAmount should increase reporting frequency
    await r.oracle.write("updateStakeAmount", _amount=int(10e18), **txn_kwargs)
    stake_amount, status = await r.oracle.read("getStakeAmount")
    assert status.ok
    assert stake_amount == int(10e18)

    assert r.staker_info.stake_balance == int(20e18)

    await r.report_once()
    assert "Currently in reporter lock. Time left: 5:59" in caplog.text  # 6hr


@pytest.mark.asyncio
async def test_get_time_based_rewards(tellor_360, caplog):

    contracts, _ = tellor_360
    tbr = await get_time_based_rewards(contracts.oracle)

    assert tbr >= 0
    assert isinstance(tbr, int)
    assert "not found in contract abi" not in caplog.text


@pytest.mark.asyncio
async def test_360_reporter_rewards(tellor_360, caplog):

    contracts, account = tellor_360

    r = Tellor360Reporter(
        oracle=contracts.oracle,
        token=contracts.token,
        autopay=contracts.autopay,
        endpoint=contracts.oracle.node,
        account=account,
        chain_id=CHAIN_ID,
        transaction_type=0,
    )

    assert isinstance(await r.rewards(), int)


@pytest.mark.asyncio
async def test_adding_stake(tellor_360):
    """Test 360 reporter depositing more stake"""
    contracts, account = tellor_360

    reporter_kwargs = {
        "oracle": contracts.oracle,
        "token": contracts.token,
        "autopay": contracts.autopay,
        "endpoint": contracts.oracle.node,
        "account": account,
        "chain_id": CHAIN_ID,
        "transaction_type": 0,
    }
    reporter = Tellor360Reporter(**reporter_kwargs)

    # check stake amount
    stake_amount, status = await reporter.oracle.read("getStakeAmount")
    assert status.ok
    assert stake_amount == int(1e18), "Should be 1e18"

    # check default stake value
    assert reporter.stake == 0

    # first should deposits default stake
    _, status = await reporter.report_once()
    assert status.ok
    assert reporter.staker_info.stake_balance == int(1e18), "Staker balance should be 1e18"

    # stake more by by changing stake from default similar to how a stake amount chosen in cli
    # high stake to bypass reporter lock
    reporter = Tellor360Reporter(**reporter_kwargs, stake=90000)
    _, status = await reporter.report_once()
    assert status.ok
    assert reporter.staker_info.stake_balance == pytest.approx(90000e18), "Staker balance should be 90000e18"


@pytest.mark.asyncio
async def test_no_native_token(tellor_360, caplog):
    """Test reporter quits if no native token"""
    contracts, account = tellor_360

    reporter_kwargs = {
        "oracle": contracts.oracle,
        "token": contracts.token,
        "autopay": contracts.autopay,
        "endpoint": contracts.oracle.node,
        "account": account,
        "chain_id": CHAIN_ID,
        "transaction_type": 0,
        "wait_period": 0,
        "min_native_token_balance": 2 * 10**18,
    }
    reporter = Tellor360Reporter(**reporter_kwargs)

    await reporter.report(report_count=1)

    expected = f"Account {account.address} has insufficient native token funds".lower()
    assert expected in caplog.text.lower()
