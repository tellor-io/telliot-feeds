"""
Tests covering the IntervalReporter class from
telliot's reporters subpackage.
"""
import asyncio
from datetime import datetime
from unittest import mock

import pytest
from telliot_core.gas.legacy_gas import ethgasstation
from telliot_core.utils.response import ResponseStatus
from web3.datastructures import AttributeDict

from telliot_feeds.datafeed import DataFeed
from telliot_feeds.feeds.eth_usd_feed import eth_usd_median_feed
from telliot_feeds.reporters import interval
from telliot_feeds.sources.etherscan_gas import EtherscanGasPrice
from tests.utils.utils import gas_price
from tests.utils.utils import passing_bool_w_status
from tests.utils.utils import passing_status


@pytest.mark.asyncio
async def test_fetch_datafeed(tellor_flex_reporter):
    r = tellor_flex_reporter
    feed = await r.fetch_datafeed()
    assert isinstance(feed, DataFeed)

    r.datafeed = None
    assert r.datafeed is None
    feed = await r.fetch_datafeed()
    assert isinstance(feed, DataFeed)


@pytest.mark.asyncio
async def test_get_fee_info(tellor_flex_reporter):
    info, time = await tellor_flex_reporter.get_fee_info()

    assert isinstance(time, datetime)
    assert isinstance(info, EtherscanGasPrice)
    assert isinstance(info.LastBlock, int)
    assert info.LastBlock > 0
    assert isinstance(info.gasUsedRatio, list)


@pytest.mark.asyncio
async def test_get_num_reports_by_id(tellor_flex_reporter):
    r = tellor_flex_reporter
    num, status = await r.get_num_reports_by_id(eth_usd_median_feed.query.query_id)

    assert isinstance(status, ResponseStatus)

    if status.ok:
        assert isinstance(num, int)
    else:
        assert num is None


@pytest.mark.asyncio
async def test_ensure_staked(tellor_flex_reporter):
    """Test staking status of reporter."""
    staked, status = await tellor_flex_reporter.ensure_staked()

    assert staked
    assert status.ok


@pytest.mark.asyncio
async def test_check_reporter_lock(tellor_flex_reporter):
    """Test checking if in reporter lock."""
    r = tellor_flex_reporter
    r.last_submission_timestamp = 0

    status = await r.check_reporter_lock()

    assert isinstance(status, ResponseStatus)
    if not status.ok:
        assert status.error == "Current address is in reporter lock."
        assert r.last_submission_timestamp != 0


@pytest.mark.asyncio
async def test_ensure_profitable(tellor_flex_reporter):
    """Test profitability check."""
    r = tellor_flex_reporter

    assert r.expected_profit == "YOLO"

    status = await r.ensure_profitable(r.datafeed)

    assert status.ok

    r.expected_profit = 1e10
    status = await r.ensure_profitable(r.datafeed)

    assert not status.ok
    assert status.error == "Estimated profitability below threshold."


@pytest.mark.asyncio
async def test_fetch_gas_price(tellor_flex_reporter):
    """Test retrieving custom gas price from eth gas station."""
    r = tellor_flex_reporter

    assert r.gas_price_speed == "safeLow"

    r.gas_price_speed = "average"

    assert r.gas_price_speed != "safeLow"

    gas_price = await r.fetch_gas_price()

    assert isinstance(gas_price, int)
    assert gas_price > 0


@pytest.mark.asyncio
async def test_ethgasstation_error(tellor_flex_reporter):
    async def no_gas_price(speed):
        return None

    r = tellor_flex_reporter
    interval.ethgasstation = no_gas_price

    staked, status = await r.ensure_staked()
    assert not staked
    assert not status.ok

    status = await r.ensure_profitable(eth_usd_median_feed)
    assert not status.ok

    tx_receipt, status = await r.report_once()
    assert tx_receipt is None
    assert not status.ok
    interval.ethgasstation = ethgasstation


@pytest.mark.asyncio
async def test_interval_reporter_submit_once(tellor_flex_reporter):
    """Test reporting once to the TellorX playground on Rinkeby
    with three retries."""
    r = tellor_flex_reporter

    # Sync reporter
    r.datafeed = None

    EXPECTED_ERRORS = {
        "Current addess disputed. Switch address to continue reporting.",
        "Current address is locked in dispute or for withdrawal.",
        "Current address is in reporter lock.",
        "Estimated profitability below threshold.",
        "Estimated gas price is above maximum gas price.",
        "Unable to retrieve updated datafeed value.",
    }

    ORACLE_ADDRESSES = {r.oracle.address}

    tx_receipt, status = await r.report_once()

    # Reporter submitted
    if tx_receipt is not None and status.ok:
        assert isinstance(tx_receipt, AttributeDict)
        assert tx_receipt.to in ORACLE_ADDRESSES
    # Reporter did not submit
    else:
        assert not tx_receipt
        assert not status.ok
        assert status.error in EXPECTED_ERRORS


@pytest.mark.asyncio
async def test_no_updated_value(tellor_flex_reporter, bad_datasource):
    """Test handling for no updated value returned from datasource."""
    r = tellor_flex_reporter

    # Clear latest datapoint
    r.datafeed.source._history.clear()

    # Replace PriceAggregator's sources with test source that
    # returns no updated DataPoint
    r.datafeed.source.sources = [bad_datasource]

    r.fetch_gas_price = gas_price
    r.check_reporter_lock = passing_status
    r.ensure_profitable = passing_status

    tx_receipt, status = await r.report_once()

    assert not tx_receipt
    assert not status.ok
    print("status.error:", status.error)
    assert status.error == "Unable to retrieve updated datafeed value."


@pytest.mark.asyncio
async def test_no_token_prices_for_profit_calc(tellor_flex_reporter, bad_datasource, guaranteed_price_source):
    """Test handling for no token prices for profit calculation."""
    r = tellor_flex_reporter

    r.fetch_gas_price = gas_price
    r.check_reporter_lock = passing_status

    # Simulate TRB/USD price retrieval failure
    r.trb_usd_median_feed.source._history.clear()
    r.eth_usd_median_feed.source.sources = [guaranteed_price_source]
    r.trb_usd_median_feed.source.sources = [bad_datasource]
    tx_receipt, status = await r.report_once()

    assert tx_receipt is None
    assert not status.ok
    assert status.error == "Unable to fetch TRB/USD price for profit calculation"

    # Simulate ETH/USD price retrieval failure
    r.eth_usd_median_feed.source._history.clear()
    r.eth_usd_median_feed.source.sources = [bad_datasource]
    tx_receipt, status = await r.report_once()

    assert tx_receipt is None
    assert not status.ok
    assert status.error == "Unable to fetch ETH/USD price for profit calculation"


@pytest.mark.asyncio
async def test_handle_contract_master_read_timeout(tellor_flex_reporter):
    """Test handling for contract master read timeout."""

    def conn_timeout(url, *args, **kwargs):
        raise asyncio.exceptions.TimeoutError()

    with mock.patch("web3.contract.ContractFunction.call", side_effect=conn_timeout):
        r = tellor_flex_reporter
        r.fetch_gas_price = gas_price
        staked, status = await r.ensure_staked()

        assert not staked
        assert not status.ok
        assert "Unable to read reporters staker status" in status.error


@pytest.mark.asyncio
async def test_ensure_reporter_lock_check_after_submitval_attempt(
    monkeypatch, tellor_flex_reporter, guaranteed_price_source
):
    r = tellor_flex_reporter
    r.last_submission_timestamp = 1234
    r.fetch_gas_price = gas_price
    r.ensure_staked = passing_bool_w_status
    r.ensure_profitable = passing_status

    assert r.datafeed

    # Simulate fetching latest value
    r.eth_usd_median_feed.source.sources = [guaranteed_price_source]
    r.trb_usd_median_feed.source.sources = [guaranteed_price_source]
    r.datafeed.source.sources = [guaranteed_price_source]

    async def num_reports(*args, **kwargs):
        return 1, ResponseStatus()

    r.get_num_reports_by_id = num_reports

    assert r.last_submission_timestamp == 1234

    def send_failure(*args, **kwargs):
        raise Exception("bingo")

    with mock.patch("web3.eth.Eth.send_raw_transaction", side_effect=send_failure):
        tx_receipt, status = await r.report_once()
        assert tx_receipt is None
        assert not status.ok
        assert "bingo" in status.error
        assert r.last_submission_timestamp == 0
