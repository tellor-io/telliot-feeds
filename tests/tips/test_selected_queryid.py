import pytest
from brownie import chain
from eth_utils import to_bytes
from telliot_core.apps.core import TelliotCore

from telliot_feeds.feeds.matic_usd_feed import matic_usd_median_feed
from telliot_feeds.reporters.tellor_360 import Tellor360Reporter
from telliot_feeds.reporters.tips.tip_amount import fetch_feed_tip


query_data = matic_usd_median_feed.query.query_data
query_id = matic_usd_median_feed.query.query_id
reward = 1 * 10**18
interval = 100
window = 99
price_threshold = 0
start_time = chain.time()
txn_kwargs = {
    "gas_limit": 3500000,
    "legacy_gas_price": 1,
    "_queryId": query_id,
    "_queryData": query_data,
}
setup_datafeed_kwargs_big_window = {
    "_reward": reward,
    "_startTime": start_time,
    "_interval": interval,
    "_window": window,
    "_rewardIncreasePerSecond": 0,
    "_amount": int(5 * 10**18),
}


@pytest.mark.asyncio
async def test_single_feed(autopay_contract_setup):
    """Test price threshold == 0"""
    flex = await autopay_contract_setup

    # setup and fund a feed on autopay
    _, _ = await flex.autopay.write(
        "setupDataFeed",
        **txn_kwargs,
        **setup_datafeed_kwargs_big_window,
        _priceThreshold=price_threshold,
    )
    tip_amount = await fetch_feed_tip(autopay=flex.autopay, datafeed=matic_usd_median_feed, timestamp=chain.time() + 4)
    assert tip_amount == reward


@pytest.mark.asyncio
async def test_priceThreshold_gt_zero(autopay_contract_setup):
    """Test price threshold > 0, not meeth the threshold and not first in window"""
    r = await autopay_contract_setup
    price_threshold = int(1e18)

    # setup and fund a feed on autopay
    _, _ = await r.autopay.write(
        "setupDataFeed",
        **txn_kwargs,
        **setup_datafeed_kwargs_big_window,
        _priceThreshold=price_threshold,
    )
    get_price = await matic_usd_median_feed.source.fetch_new_datapoint()
    price = get_price[0]
    tip_amount = await fetch_feed_tip(autopay=r.autopay, datafeed=matic_usd_median_feed)
    assert tip_amount == reward
    await r.oracle.write(
        "submitValue",
        gas_limit=3500000,
        legacy_gas_price=1,
        _queryId=query_id,
        _value=to_bytes(int(price * 1e18)).rjust(32, b"\0"),
        _nonce=0,
        _queryData=query_data,
    )
    tip_amount = await fetch_feed_tip(autopay=r.autopay, datafeed=matic_usd_median_feed, timestamp=chain.time() + 2)
    assert tip_amount == 0


@pytest.mark.asyncio
async def test_ousideof_window_pt0(autopay_contract_setup):
    """Test price threshold == 0 outside of window"""
    r = await autopay_contract_setup
    interval = 20
    window = 1
    # setup and fund a feed on autopay
    _, _ = await r.autopay.write(
        "setupDataFeed",
        **txn_kwargs,
        _reward=reward,
        _startTime=start_time,
        _interval=interval,
        _window=window,
        _priceThreshold=price_threshold,
        _rewardIncreasePerSecond=0,
        _amount=int(5 * 10**18),
    )
    chain.mine(timedelta=1)
    tip_amount = await fetch_feed_tip(autopay=r.autopay, datafeed=matic_usd_median_feed, timestamp=chain.time())
    assert tip_amount == 0


@pytest.mark.asyncio
async def test_priceThreshold_zero(autopay_contract_setup):
    """Test price threshold = 0 and not first in window"""
    r = await autopay_contract_setup
    # setup and fund a feed on autopay
    _, _ = await r.autopay.write(
        "setupDataFeed",
        **txn_kwargs,
        **setup_datafeed_kwargs_big_window,
        _priceThreshold=price_threshold,
    )
    tip_amount = await fetch_feed_tip(autopay=r.autopay, datafeed=matic_usd_median_feed)
    assert tip_amount == reward
    await r.oracle.write(
        "submitValue",
        **txn_kwargs,
        _value=to_bytes(int(10 * 1e18)).rjust(32, b"\0"),
        _nonce=0,
    )
    tip_amount = await fetch_feed_tip(autopay=r.autopay, datafeed=matic_usd_median_feed, timestamp=chain.time() + 1)
    assert tip_amount == 0


@pytest.mark.asyncio
async def test_meet_priceThreshold(autopay_contract_setup):
    """Test price threshold > 0 and not first in window but meets threshold"""
    r = await autopay_contract_setup
    price_threshold = 1

    # setup and fund a feed on autopay
    _, _ = await r.autopay.write(
        "setupDataFeed",
        **txn_kwargs,
        **setup_datafeed_kwargs_big_window,
        _priceThreshold=price_threshold,
    )
    tip_amount = await fetch_feed_tip(autopay=r.autopay, datafeed=matic_usd_median_feed)
    assert tip_amount == reward
    get_price = await matic_usd_median_feed.source.fetch_new_datapoint()
    # report a price that is 1 less than the current price so that threshold is met
    price = get_price[0] - 1
    # report a price that is falls within the interval
    await r.oracle.write(
        "submitValue",
        **txn_kwargs,
        _value=int(price * 1e18).to_bytes(32, "big", signed=True),
        _nonce=0,
    )
    # tip amount should be > 0 since price threshold is met
    tip_amount = await fetch_feed_tip(autopay=r.autopay, datafeed=matic_usd_median_feed, timestamp=chain.time() + 2)
    assert tip_amount == reward


@pytest.mark.asyncio
async def test_onetimetip_and_feedtip(autopay_contract_setup):
    """Test pt = 0 and first in window for single tip and feed"""
    r = await autopay_contract_setup
    # setup and fund a feed on autopay
    _, _ = await r.autopay.write(
        "setupDataFeed",
        **txn_kwargs,
        **setup_datafeed_kwargs_big_window,
        _priceThreshold=price_threshold,
    )

    await r.autopay.write(
        "tip",
        **txn_kwargs,
        _amount=reward,
    )
    tip_amount = await fetch_feed_tip(autopay=r.autopay, datafeed=matic_usd_median_feed, timestamp=chain.time() + 2)
    assert tip_amount == reward * 2

    # submit value within window
    await r.oracle.write(
        "submitValue",
        **txn_kwargs,
        _value=to_bytes(int(2 * 1e18)).rjust(32, b"\0"),
        _nonce=0,
    )
    tip_amount = await fetch_feed_tip(autopay=r.autopay, datafeed=matic_usd_median_feed, timestamp=chain.time() + 2)
    # tip should be 0 since there is a submission
    assert tip_amount == 0


@pytest.mark.asyncio
async def test_onetimetip_and_feedtip_pt_gt0(autopay_contract_setup):
    """Test pt > 0 and first in window for single tip and feed
    and meets threshold after submission reward should be 10"""
    r = await autopay_contract_setup
    # setup and fund a feed on autopay
    price_threshold = 1
    _, _ = await r.autopay.write(
        "setupDataFeed",
        **txn_kwargs,
        **setup_datafeed_kwargs_big_window,
        _priceThreshold=price_threshold,
    )

    await r.autopay.write(
        "tip",
        **txn_kwargs,
        _amount=reward,
    )
    tip_amount = await fetch_feed_tip(autopay=r.autopay, datafeed=matic_usd_median_feed, timestamp=chain.time() + 2)
    assert tip_amount == reward * 2

    # submit value within window
    await r.oracle.write(
        "submitValue",
        **txn_kwargs,
        _value=to_bytes(int(2 * 1e18)).rjust(32, b"\0"),
        _nonce=0,
    )
    tip_amount = await fetch_feed_tip(autopay=r.autopay, datafeed=matic_usd_median_feed, timestamp=chain.time() + 2)
    # tip should be 10 since price threshold is met and there is an in window submission
    assert tip_amount == reward


@pytest.mark.asyncio
async def test_rng(autopay_contract_setup, mumbai_test_cfg, caplog):
    """Test RNG tip and submission"""
    flex = await autopay_contract_setup
    core = TelliotCore(config=mumbai_test_cfg)
    account = core.get_account()
    reporter = Tellor360Reporter(
        oracle=flex.oracle,
        token=flex.token,
        autopay=flex.autopay,
        endpoint=core.endpoint,
        account=account,
        chain_id=80001,
        transaction_type=0,
        expected_profit=100,
        ignore_tbr=False,
    )
    rng_query_data = "0x00000000000000000000000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000080000000000000000000000000000000000000000000000000000000000000000954656c6c6f72524e4700000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000006346ed0f"  # noqa: E501
    rng_query_id = "0x8338de3d3a11d3e534fce36b0bf41f4ccc00f6ecd89ec5b486fb1ae529d93261"
    await reporter.autopay.write(
        "tip",
        gas_limit=3500000,
        legacy_gas_price=1,
        _queryId=rng_query_id,
        _queryData=rng_query_data,
        _amount=int(1e18),
    )
    _, status = await reporter.report_once()
    assert '{"type":"TellorRNG","timestamp":1665592591}' in caplog.text
    assert status.ok


@pytest.mark.asyncio
async def test_skip_manual_feed(autopay_contract_setup, mumbai_test_cfg, caplog):
    """Test skip manual feed"""
    flex = await autopay_contract_setup
    core = TelliotCore(config=mumbai_test_cfg)
    account = core.get_account()
    reporter = Tellor360Reporter(
        oracle=flex.oracle,
        token=flex.token,
        autopay=flex.autopay,
        endpoint=core.endpoint,
        account=account,
        chain_id=80001,
        transaction_type=0,
        expected_profit=100,
        ignore_tbr=False,
        skip_manual_feeds=True,
    )
    jai_usd_query_data = "0x00000000000000000000000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000080000000000000000000000000000000000000000000000000000000000000000953706f745072696365000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000c00000000000000000000000000000000000000000000000000000000000000040000000000000000000000000000000000000000000000000000000000000008000000000000000000000000000000000000000000000000000000000000000036a6169000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000037573640000000000000000000000000000000000000000000000000000000000"  # noqa: E501
    jai_usd_query_id = "0x8cad613ed5dbbcb23c028a6656cb051a1adf2954c8aaa4cb834b1e7e45069ca4"
    await reporter.autopay.write(
        "tip",
        gas_limit=3500000,
        legacy_gas_price=1,
        _queryId=jai_usd_query_id,
        _queryData=jai_usd_query_data,
        _amount=int(1e18),
    )
    _, status = await reporter.report_once()
    assert not status.ok
    assert f"There is a tip for this query type: SpotPrice. Query data: {jai_usd_query_data[2:]}" in caplog.text

    eth_usd_query_data = "0x00000000000000000000000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000080000000000000000000000000000000000000000000000000000000000000000953706F745072696365000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000C0000000000000000000000000000000000000000000000000000000000000004000000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000003657468000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000037573640000000000000000000000000000000000000000000000000000000000"  # noqa: E501
    eth_usd_query_id = "0x83A7F3D48786AC2667503A61E8C415438ED2922EB86A2906E4EE66D9A2CE4992"
    # report for eth_usd should work
    await reporter.autopay.write(
        "tip",
        gas_limit=3500000,
        legacy_gas_price=1,
        _queryId=eth_usd_query_id,
        _queryData=eth_usd_query_data,
        _amount=int(1e18),
    )
    _, status = await reporter.report_once()
    assert status.ok
