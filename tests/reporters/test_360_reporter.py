import datetime
import math
import time
from unittest import mock
from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest
from brownie import accounts
from brownie import chain

from telliot_feeds.feeds.eth_usd_feed import eth_usd_median_feed
from telliot_feeds.feeds.matic_usd_feed import matic_usd_median_feed
from telliot_feeds.feeds.snapshot_feed import snapshot_manual_feed
from telliot_feeds.feeds.trb_usd_feed import trb_usd_median_feed
from telliot_feeds.reporters.rewards.time_based_rewards import get_time_based_rewards
from telliot_feeds.reporters.tellor_360 import Tellor360Reporter


txn_kwargs = {"gas_limit": 3500000, "legacy_gas_price": 1}
CHAIN_ID = 80001


@pytest.mark.asyncio
async def test_report(tellor_360, caplog, guaranteed_price_source, mock_flex_contract, mock_token_contract):
    """Test 360 reporter deposit and balance changes when stakeAmount changes"""
    contracts, account = tellor_360
    feed = eth_usd_median_feed
    feed.source = guaranteed_price_source

    r = Tellor360Reporter(
        oracle=contracts.oracle,
        token=contracts.token,
        autopay=contracts.autopay,
        endpoint=contracts.oracle.node,
        account=account,
        chain_id=CHAIN_ID,
        transaction_type=0,
        min_native_token_balance=0,
        datafeed=feed,
        check_rewards=False,
        ignore_tbr=False,
    )

    await r.report_once()
    assert r.staker_info.stake_balance == int(10e18)
    # report count before first submission
    assert r.staker_info.reports_count == 0

    # update stakeamount increase causes reporter to deposit more to keep reporting
    mock_token_contract.faucet(accounts[0].address)
    mock_token_contract.approve(mock_flex_contract.address, mock_flex_contract.stakeAmount())
    mock_flex_contract.depositStake(mock_flex_contract.stakeAmount())
    mock_flex_contract.submitValue(
        trb_usd_median_feed.query.query_id,
        "0x0000000000000000000000000000000000000000000000004563918244f40000",
        0,
        trb_usd_median_feed.query.query_data,
    )
    chain.sleep(86400)
    mock_flex_contract.updateStakeAmount()
    chain.mine(1, timedelta=1)
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
    mock_token_contract.approve(mock_flex_contract.address, mock_flex_contract.stakeAmount())
    mock_flex_contract.depositStake(mock_flex_contract.stakeAmount())
    mock_flex_contract.submitValue(
        trb_usd_median_feed.query.query_id,
        "0x00000000000000000000000000000000000000000000021e19e0c9bab2400000",
        0,
        trb_usd_median_feed.query.query_data,
    )
    chain.sleep(86400)
    mock_flex_contract.updateStakeAmount()

    stake_amount, status = await r.oracle.read("getStakeAmount")
    assert status.ok
    assert stake_amount == int(10e18)

    assert r.staker_info.stake_balance == int(20e18)

    await r.report_once()
    assert "Currently in reporter lock. Time left: 5:59" in caplog.text  # 6hr


@pytest.mark.asyncio
async def test_fail_get_account_nonce(tellor_360, caplog, guaranteed_price_source):
    """Test 360 reporter fails to retrieve account nonce"""
    contracts, account = tellor_360
    feed = eth_usd_median_feed
    feed.source = guaranteed_price_source

    r = Tellor360Reporter(
        oracle=contracts.oracle,
        token=contracts.token,
        autopay=contracts.autopay,
        endpoint=contracts.oracle.node,
        account=account,
        chain_id=CHAIN_ID,
        transaction_type=0,
        min_native_token_balance=0,
        datafeed=feed,
        ignore_tbr=False,
    )

    def mock_raise(*args, **kwargs):
        raise ValueError()

    with mock.patch("web3.eth.Eth.get_transaction_count", side_effect=mock_raise):
        val, status = r.get_acct_nonce()
        assert not status.ok
        assert val is None
        assert "Account nonce request timed out" in caplog.text

    class UnknownException(Exception):
        pass

    def mock_raise_unknown(*args, **kwargs):
        raise UnknownException()

    with mock.patch("web3.eth.Eth.get_transaction_count", side_effect=mock_raise_unknown):
        val, status = r.get_acct_nonce()
        assert not status.ok
        assert val is None
        assert "Unable to retrieve account nonce: UnknownException" in caplog.text


@pytest.mark.asyncio
async def test_get_time_based_rewards(tellor_360, caplog):

    contracts, _ = tellor_360
    tbr = await get_time_based_rewards(contracts.oracle)

    assert tbr >= 0
    assert isinstance(tbr, int)
    assert "not found in contract abi" not in caplog.text


@pytest.mark.asyncio
async def test_360_reporter_rewards(tellor_360, guaranteed_price_source):

    contracts, account = tellor_360
    feed = eth_usd_median_feed
    feed.source = guaranteed_price_source

    r = Tellor360Reporter(
        oracle=contracts.oracle,
        token=contracts.token,
        autopay=contracts.autopay,
        endpoint=contracts.oracle.node,
        account=account,
        chain_id=CHAIN_ID,
        transaction_type=0,
        min_native_token_balance=0,
        ignore_tbr=False,
        datafeed=feed,
    )

    assert isinstance(await r.rewards(), int)


@pytest.mark.asyncio
async def test_adding_stake(tellor_360, guaranteed_price_source):
    """Test 360 reporter depositing more stake"""
    contracts, account = tellor_360
    feed = eth_usd_median_feed
    feed.source = guaranteed_price_source

    reporter_kwargs = {
        "oracle": contracts.oracle,
        "token": contracts.token,
        "autopay": contracts.autopay,
        "endpoint": contracts.oracle.node,
        "account": account,
        "chain_id": CHAIN_ID,
        "transaction_type": 0,
        "min_native_token_balance": 0,
        "datafeed": feed,
        "ignore_tbr": False,
    }
    reporter = Tellor360Reporter(**reporter_kwargs)

    # check stake amount
    stake_amount, status = await reporter.oracle.read("getStakeAmount")
    assert status.ok
    assert stake_amount == int(10e18), "Should be 10e18"

    # check default stake value
    assert reporter.stake == 0

    # first should deposits default stake
    _, status = await reporter.report_once()
    assert status.ok
    assert reporter.staker_info.stake_balance == int(10e18), "Staker balance should be 10e18"

    # stake more by by changing stake from default similar to how a stake amount chosen in cli
    # high stake to bypass reporter lock
    reporter = Tellor360Reporter(**reporter_kwargs, stake=900000)
    _, status = await reporter.report_once()
    assert status.ok
    assert reporter.staker_info.stake_balance == pytest.approx(900000e18), "Staker balance should be 90000e18"


@pytest.mark.asyncio
async def test_no_native_token(tellor_360, caplog, guaranteed_price_source):
    """Test reporter quits if no native token"""
    contracts, account = tellor_360
    feed = eth_usd_median_feed
    feed.source = guaranteed_price_source

    reporter_kwargs = {
        "oracle": contracts.oracle,
        "token": contracts.token,
        "autopay": contracts.autopay,
        "endpoint": contracts.oracle.node,
        "account": account,
        "chain_id": CHAIN_ID,
        "transaction_type": 0,
        "wait_period": 0,
        "min_native_token_balance": 100 * 10**18,
        "datafeed": feed,
        "ignore_tbr": False,
    }
    reporter = Tellor360Reporter(**reporter_kwargs)

    await reporter.report(report_count=1)

    assert "insufficient native token funds" in caplog.text.lower()


@pytest.mark.asyncio
async def test_checks_reporter_lock_when_manual_source(tellor_360, monkeypatch, caplog, guaranteed_price_source):
    """Test reporter lock check when reporting for a tip that requires a manaul data source"""
    contracts, account = tellor_360
    feed = eth_usd_median_feed
    feed.source = guaranteed_price_source

    reporter_kwargs = {
        "oracle": contracts.oracle,
        "token": contracts.token,
        "autopay": contracts.autopay,
        "endpoint": contracts.oracle.node,
        "account": account,
        "chain_id": CHAIN_ID,
        "transaction_type": 0,
        "wait_period": 0,
        "min_native_token_balance": 0,
        "datafeed": feed,
        "ignore_tbr": False,
    }

    # mock get_feed_and_tip, which is called in the Tellor360Reporter.fetch_datafeed method
    async def mock_get_feed_and_tip(*args, **kwargs):
        return [snapshot_manual_feed, int(1e18)]

    with monkeypatch.context() as m:
        m.setattr("telliot_feeds.reporters.tellor_360.get_feed_and_tip", mock_get_feed_and_tip)
        reporter = Tellor360Reporter(**reporter_kwargs)

        # report once to trigger reporter lock next time
        reporter.datafeed = eth_usd_median_feed
        _, status = await reporter.report_once()
        assert status.ok

        # set datafeed to None so fetch_datafeed will call get_feed_and_tip
        reporter.datafeed = None
        await reporter.report(report_count=1)
        reporter_lock = 43200 / math.floor(reporter.staker_info.stake_balance / reporter.stake_amount)
        time_remaining = round(reporter.staker_info.last_report + reporter_lock - time.time())
        if time_remaining > 0:
            hr_min_sec = str(datetime.timedelta(seconds=time_remaining))
        assert f"Currently in reporter lock. Time left: {hr_min_sec}" in caplog.text


@pytest.mark.asyncio
async def test_fail_gen_query_id(tellor_360, caplog, guaranteed_price_source):
    """Test failure to generate query id when calling rewards() method."""
    contracts, account = tellor_360
    feed = eth_usd_median_feed
    feed.source = guaranteed_price_source

    reporter_kwargs = {
        "oracle": contracts.oracle,
        "token": contracts.token,
        "autopay": contracts.autopay,
        "endpoint": contracts.oracle.node,
        "account": account,
        "chain_id": CHAIN_ID,
        "transaction_type": 0,
        "wait_period": 0,
        "min_native_token_balance": 0,
        "datafeed": feed,
        "ignore_tbr": False,
    }

    # This will cause the SpotPrice query to throw an eth_abi.exceptions.EncodingTypeError when
    # trying to generate the query data for the query id.
    eth_usd_median_feed.query.asset = None

    reporter = Tellor360Reporter(**reporter_kwargs)
    _ = await reporter.rewards()

    assert "Unable to generate data/id for query" in caplog.text


@pytest.mark.asyncio
async def test_tbr_tip_increment(tellor_360, guaranteed_price_source, caplog, chain):
    contracts, account = tellor_360
    feed = eth_usd_median_feed
    feed.source = guaranteed_price_source
    matic_usd_median_feed.source = guaranteed_price_source

    _ = await contracts.autopay.write(
        "tip",
        **txn_kwargs,
        _amount=1 * 10**18,
        _queryId=matic_usd_median_feed.query.query_id,
        _queryData=matic_usd_median_feed.query.query_data,
    )
    reporter_kwargs = {
        "oracle": contracts.oracle,
        "token": contracts.token,
        "autopay": contracts.autopay,
        "endpoint": contracts.oracle.node,
        "account": account,
        "chain_id": 5,  # set chain id to 5 so it checks tbr
        "transaction_type": 0,
        "wait_period": 0,
        "min_native_token_balance": 0,
        "expected_profit": 1000.0,  # set expected profit high so it won't report
        "ignore_tbr": False,
    }

    def mock_tbr():
        current_number = 0
        while True:
            yield current_number
            current_number += 1e18

    generator = mock_tbr()
    mock_async_tbr = AsyncMock(side_effect=lambda _: next(generator))

    reporter = Tellor360Reporter(**reporter_kwargs)
    assert reporter.check_rewards

    with patch("telliot_feeds.reporters.tellor_360.get_time_based_rewards", mock_async_tbr):
        await reporter.report(report_count=3)
        # tip amount should increase by 1e18 each time and not more
        assert "Fetching time based rewards" in caplog.text
        assert "Ignoring time based rewards" not in caplog.text
        assert "Tips: 1.0" in caplog.text
        assert "Tips: 2.0" in caplog.text
        assert "Tips: 3.0" in caplog.text
        caplog.clear()

        reporter.ignore_tbr = True
        await reporter.report(report_count=3)
        assert "Ignoring time based rewards" in caplog.text
        assert "Fetching time based rewards" not in caplog.text
        assert "Tips: 1.0" in caplog.text
        # tip amount should not increase
        assert "Tips: 2.0" not in caplog.text
        assert "Tips: 3.0" not in caplog.text
