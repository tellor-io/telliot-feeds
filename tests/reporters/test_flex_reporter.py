from unittest.mock import patch

import pytest
from brownie import chain
from telliot_core.utils.response import ResponseStatus

from telliot_feeds.datafeed import DataFeed
from telliot_feeds.feeds import CATALOG_FEEDS
from telliot_feeds.feeds.matic_usd_feed import matic_usd_median_feed
from telliot_feeds.reporters.tellor_flex import TellorFlexReporter


@pytest.mark.asyncio
async def test_YOLO_feed_suggestion(tellor_flex_reporter):
    tellor_flex_reporter.expected_profit = "YOLO"
    feed = await tellor_flex_reporter.fetch_datafeed()

    assert feed is not None
    assert isinstance(feed, DataFeed)


@pytest.mark.asyncio
async def test_ensure_profitable(tellor_flex_reporter):
    r = tellor_flex_reporter
    r.expected_profit = "YOLO"
    r.gas_info = {"type": 0, "gas_price": 1e9, "gas_limit": 300000}
    unused_feed = matic_usd_median_feed
    status = await r.ensure_profitable(unused_feed)

    assert isinstance(status, ResponseStatus)
    assert status.ok

    r.chain_id = 1
    r.expected_profit = 100.0
    status = await r.ensure_profitable(unused_feed)

    assert not status.ok


@pytest.mark.asyncio
async def test_fetch_gas_price(tellor_flex_reporter):
    price = await tellor_flex_reporter.fetch_gas_price()

    assert isinstance(price, float)
    assert price > 0


@pytest.mark.asyncio
async def test_ensure_staked(tellor_flex_reporter):
    staked, status = await tellor_flex_reporter.ensure_staked()

    assert isinstance(status, ResponseStatus)
    assert isinstance(staked, bool)
    if status.ok:
        assert staked
    else:
        assert "Unable to approve staking" in status.error


@pytest.mark.asyncio
async def test_check_reporter_lock(tellor_flex_reporter):
    status = await tellor_flex_reporter.check_reporter_lock()

    assert isinstance(status, ResponseStatus)
    if not status.ok:
        assert ("reporter lock" in status.error) or ("Staker balance too low" in status.error)


@pytest.mark.asyncio
async def test_get_num_reports_by_id(tellor_flex_reporter):
    qid = matic_usd_median_feed.query.query_id
    count, status = await tellor_flex_reporter.get_num_reports_by_id(qid)

    assert isinstance(status, ResponseStatus)
    if status.ok:
        assert isinstance(count, int)
    else:
        assert count is None


@pytest.mark.asyncio
async def test_fetch_gas_price_error(tellor_flex_reporter, caplog):
    # Test invalid gas price speed
    r = tellor_flex_reporter

    with patch("telliot_feeds.reporters.tellor_flex.TellorFlexReporter.fetch_gas_price") as func:
        func.return_value = None

        r.stake = 1e100
        staked, status = await r.ensure_staked()
        assert not staked
        assert not status.ok
        assert "Unable to fetch gas price for staking" in status.error
        _, status = await r.report_once()
        assert not status.ok
        assert "Unable to fetch gas price" in status.error


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
async def test_dispute(tellor_flex_reporter: TellorFlexReporter):
    # Test when reporter in dispute
    r = tellor_flex_reporter

    async def in_dispute(_):
        return True

    r.in_dispute = in_dispute
    _, status = await r.report_once()
    assert (
        "Staked balance has decreased, account might be in dispute; restart telliot to keep reporting" in status.error
    )


@pytest.mark.asyncio
async def test_reset_datafeed(tellor_flex_reporter):
    # Test when reporter selects qtag vs not
    # datafeed should persist if qtag selected
    r: TellorFlexReporter = tellor_flex_reporter

    reporter1 = TellorFlexReporter(
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
    reporter2 = TellorFlexReporter(
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
