import datetime
import math
import time
from unittest import mock
from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest
from brownie import accounts
from brownie import chain
from telliot_core.utils.response import error_status
from telliot_core.utils.response import ResponseStatus

from telliot_feeds.datafeed import DataFeed
from telliot_feeds.feeds import CATALOG_FEEDS
from telliot_feeds.feeds.btc_usd_feed import btc_usd_median_feed
from telliot_feeds.feeds.eth_usd_feed import eth_usd_median_feed
from telliot_feeds.feeds.matic_usd_feed import matic_usd_median_feed
from telliot_feeds.feeds.snapshot_feed import snapshot_manual_feed
from telliot_feeds.feeds.trb_usd_feed import trb_usd_median_feed
from telliot_feeds.reporters.rewards.time_based_rewards import get_time_based_rewards
from telliot_feeds.reporters.tellor_360 import Tellor360Reporter
from telliot_feeds.utils.log import get_logger
from tests.utils.utils import passing_bool_w_status

logger = get_logger(__name__)

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
    assert r.stake_info.current_staker_balance == int(10e18)
    # report count before first submission
    assert "reports count: 0" in caplog.text

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
    assert r.stake_info.current_stake_amount == stake_amount
    assert "Currently in reporter lock. Time left: 11:59" in caplog.text  # 12hr
    # report count before second report
    assert "reports count: 1" in caplog.text
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

    assert r.stake_info.current_staker_balance == int(20e18)

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
        expected_profit="YOLO",
    )

    assert isinstance(await r.rewards(), int)
    await r.report_once()


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
    assert reporter.stake_info.current_staker_balance == int(10e18), "Staker balance should be 10e18"

    # stake more by by changing stake from default similar to how a stake amount chosen in cli
    # high stake to bypass reporter lock
    reporter = Tellor360Reporter(**reporter_kwargs, stake=900000)
    _, status = await reporter.report_once()
    assert status.ok
    assert reporter.stake_info.current_staker_balance == pytest.approx(900000e18), "Staker balance should be 90000e18"


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
        reporter_lock = 43200 / math.floor(
            reporter.stake_info.current_staker_balance / reporter.stake_info.current_stake_amount
        )
        time_remaining = round(reporter.stake_info.last_report_time + reporter_lock - time.time())
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


@pytest.mark.asyncio
async def test_fetch_datafeed(tellor_flex_reporter):
    r = tellor_flex_reporter
    r.use_random_feeds = True
    feed = await r.fetch_datafeed()
    assert isinstance(feed, DataFeed)

    r.datafeed = None
    assert r.datafeed is None
    feed = await r.fetch_datafeed()
    assert isinstance(feed, DataFeed)


@pytest.mark.skip(reason="EIP-1559 not supported by ganache")
@pytest.mark.asyncio
def test_get_fee_info(tellor_flex_reporter):
    """Test fee info for type 2 transactions."""
    tellor_flex_reporter.transaction_type = 2
    tellor_flex_reporter.update_gas_fees()
    gas_fees = tellor_flex_reporter.get_gas_info()

    assert isinstance(gas_fees["maxPriorityFeePerGas"], int)
    assert isinstance(gas_fees["maxFeePerGas"], int)


@pytest.mark.asyncio
async def test_get_num_reports_by_id(tellor_flex_reporter):
    r = tellor_flex_reporter
    num, status = await r.get_num_reports_by_id(matic_usd_median_feed.query.query_id)

    assert status.ok
    assert isinstance(num, int)


@pytest.mark.asyncio
async def test_ensure_staked(tellor_flex_reporter):
    """Test staking status of reporter."""
    staked, status = await tellor_flex_reporter.ensure_staked()

    assert staked
    assert status.ok


@pytest.mark.asyncio
async def test_ensure_profitable(tellor_flex_reporter):
    """Test profitability check."""
    r = tellor_flex_reporter
    r.gas_info = {"maxPriorityFeePerGas": None, "maxFeePerGas": None, "gasPrice": 1e9, "gas": 300000}

    assert r.expected_profit == "YOLO"

    status = await r.ensure_profitable()

    assert status.ok

    r.expected_profit = 1e10
    status = await r.ensure_profitable()

    assert not status.ok
    assert status.error == "Estimated profitability below threshold."


@pytest.mark.asyncio
async def test_ethgasstation_error(tellor_flex_reporter):
    with mock.patch("telliot_feeds.reporters.tellor_360.Tellor360Reporter.update_gas_fees") as func:
        func.return_value = error_status("failed", log=logger.error)
        r = tellor_flex_reporter

        staked, status = await r.ensure_staked()
        assert not staked
        assert not status.ok


@pytest.mark.asyncio
async def test_no_updated_value(tellor_flex_reporter, bad_datasource):
    """Test handling for no updated value returned from datasource."""
    r = tellor_flex_reporter
    r.datafeed = btc_usd_median_feed

    # Clear latest datapoint
    r.datafeed.source._history.clear()

    # Replace PriceAggregator's sources with test source that
    # returns no updated DataPoint
    r.datafeed.source.sources = [bad_datasource]

    tx_receipt, status = await r.report_once()

    assert not tx_receipt
    assert not status.ok
    assert status.error == "Unable to retrieve updated datafeed value."


@pytest.mark.asyncio
async def test_ensure_reporter_lock_check_after_submitval_attempt(
    tellor_flex_reporter, guaranteed_price_source, caplog
):
    r = tellor_flex_reporter

    async def check_reporter_lock(*args, **kwargs):
        logger.debug(f"Checking reporter lock: {time.time()}")
        return ResponseStatus()

    r.ensure_staked = passing_bool_w_status
    r.check_reporter_lock = check_reporter_lock
    r.datafeed = matic_usd_median_feed
    r.gas_limit = 350000

    # Simulate fetching latest value
    r.datafeed.source.sources = [guaranteed_price_source]

    def send_failure(*args, **kwargs):
        raise Exception("bingo")

    with mock.patch("web3.eth.Eth.send_raw_transaction", side_effect=send_failure):
        r.wait_period = 0
        await r.report(2)
        assert "Send transaction failed: Exception('bingo')" in caplog.text
        assert caplog.text.count("Checking reporter lock") == 2


@pytest.mark.asyncio
async def test_check_reporter_lock(tellor_flex_reporter):
    status = await tellor_flex_reporter.check_reporter_lock()

    assert isinstance(status, ResponseStatus)
    if not status.ok:
        assert ("reporter lock" in status.error) or ("Staker balance too low" in status.error)


@pytest.mark.asyncio
async def test_reporting_without_internet(tellor_flex_reporter, caplog):
    async def offline():
        return False

    with patch("asyncio.sleep", side_effect=InterruptedError):
        r = tellor_flex_reporter
        r.is_online = lambda: offline()
        with pytest.raises(InterruptedError):
            await r.report()
        assert "Unable to connect to the internet!" in caplog.text


@pytest.mark.asyncio
async def test_dispute(tellor_flex_reporter, caplog):
    # Test when reporter in dispute
    r = tellor_flex_reporter
    r.datafeed = matic_usd_median_feed
    # initial balance higher than current balance, current balance is 0 since first time staking
    r.stake_info.store_staker_balance(1)

    _ = await r.report_once()
    assert "Your staked balance has decreased, account might be in dispute" in caplog.text


@pytest.mark.asyncio
async def test_reset_datafeed(tellor_flex_reporter):
    # Test when reporter selects qtag vs not
    # datafeed should persist if qtag selected
    r = tellor_flex_reporter

    reporter1 = Tellor360Reporter(
        oracle=r.oracle,
        token=r.token,
        autopay=r.autopay,
        endpoint=r.endpoint,
        account=r.account,
        chain_id=80001,
        transaction_type=0,
        datafeed=CATALOG_FEEDS["trb-usd-spot"],
        min_native_token_balance=0,
    )
    reporter2 = Tellor360Reporter(
        oracle=r.oracle,
        token=r.token,
        autopay=r.autopay,
        endpoint=r.endpoint,
        account=r.account,
        chain_id=80001,
        transaction_type=0,
        min_native_token_balance=0,
    )

    # Unlocker reporter lock checker
    async def reporter_lock():
        return ResponseStatus()

    reporter1.check_reporter_lock = lambda: reporter_lock()
    reporter2.check_reporter_lock = lambda: reporter_lock()

    async def reprt():
        for _ in range(3):
            await reporter1.report_once()
            assert reporter1.qtag_selected is True
            assert reporter1.datafeed.query.asset == "trb"
            chain.sleep(43201)

        for _ in range(3):
            await reporter2.report_once()
            assert reporter2.qtag_selected is False
            chain.sleep(43201)

    _ = await reprt()
