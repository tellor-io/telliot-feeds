"""
Tests covering the IntervalReporter class from
telliot's reporters subpackage.
"""
import asyncio
from datetime import datetime
from unittest import mock

import pytest
import pytest_asyncio
from brownie import accounts
from telliot_core.apps.core import TelliotCore
from telliot_core.gas.legacy_gas import ethgasstation
from telliot_core.utils.response import ResponseStatus
from web3.datastructures import AttributeDict

from telliot_feeds.datafeed import DataFeed
from telliot_feeds.feeds.eth_usd_feed import eth_usd_median_feed
from telliot_feeds.reporters import interval
from telliot_feeds.reporters.interval import IntervalReporter
from telliot_feeds.sources.etherscan_gas import EtherscanGasPrice


@pytest_asyncio.fixture(scope="function")
async def eth_usd_reporter(
    rinkeby_test_cfg,
    tellorx_master_mock_contract,
    tellorx_oracle_mock_contract,
):
    """Returns an instance of an IntervalReporter using
    the ETH/USD median datafeed."""
    async with TelliotCore(config=rinkeby_test_cfg) as core:
        account = core.get_account()
        tellorx = core.get_tellorx_contracts()
        tellorx.master.address = tellorx_master_mock_contract.address
        tellorx.oracle.address = tellorx_oracle_mock_contract.address
        tellorx.master.connect()
        tellorx.oracle.connect()
        r = IntervalReporter(
            endpoint=core.config.get_endpoint(),
            account=account,
            master=tellorx.master,
            oracle=tellorx.oracle,
            datafeed=eth_usd_median_feed,
            expected_profit="YOLO",
            transaction_type=0,
            gas_limit=400000,
            max_fee=None,
            priority_fee=None,
            legacy_gas_price=None,
            gas_price_speed="safeLow",
            chain_id=core.config.main.chain_id,
        )
        # send eth from brownie address to reporter address for txn fees
        accounts[1].transfer(account.address, "1 ether")
        return r


async def gas_price(speed="average"):
    return 1


async def passing_status(*args, **kwargs):
    return ResponseStatus()


async def passing_bool_w_status(*args, **kwargs):
    return True, ResponseStatus()


@pytest.mark.asyncio
async def test_fetch_datafeed(eth_usd_reporter):
    r = eth_usd_reporter
    feed = await r.fetch_datafeed()
    assert isinstance(feed, DataFeed)

    r.datafeed = None
    assert r.datafeed is None
    feed = await r.fetch_datafeed()
    assert isinstance(feed, DataFeed)


@pytest.mark.asyncio
async def test_get_fee_info(eth_usd_reporter):
    info, time = await eth_usd_reporter.get_fee_info()

    assert isinstance(time, datetime)
    assert isinstance(info, EtherscanGasPrice)
    assert isinstance(info.LastBlock, int)
    assert info.LastBlock > 0
    assert isinstance(info.gasUsedRatio, list)


@pytest.mark.asyncio
async def test_get_num_reports_by_id(eth_usd_reporter):
    r = eth_usd_reporter
    num, status = await r.get_num_reports_by_id(r.datafeed.query.query_id)

    assert isinstance(status, ResponseStatus)

    if status.ok:
        assert isinstance(num, int)
    else:
        assert num is None


@pytest.mark.asyncio
async def test_ensure_staked(eth_usd_reporter):
    """Test staking status of reporter."""
    staked, status = await eth_usd_reporter.ensure_staked()

    assert staked
    assert status.ok


@pytest.mark.asyncio
async def test_check_reporter_lock(eth_usd_reporter):
    """Test checking if in reporter lock."""
    r = eth_usd_reporter
    r.last_submission_timestamp = 0

    status = await r.check_reporter_lock()

    assert isinstance(status, ResponseStatus)
    if not status.ok:
        assert status.error == "Current address is in reporter lock."
        assert r.last_submission_timestamp != 0


@pytest.mark.asyncio
async def test_ensure_profitable(eth_usd_reporter):
    """Test profitability check."""
    r = eth_usd_reporter

    assert r.expected_profit == "YOLO"

    status = await r.ensure_profitable(r.datafeed)

    assert status.ok

    r.expected_profit = 1e10
    status = await r.ensure_profitable(r.datafeed)

    assert not status.ok
    assert status.error == "Estimated profitability below threshold."


@pytest.mark.asyncio
async def test_fetch_gas_price(eth_usd_reporter):
    """Test retrieving custom gas price from eth gas station."""
    r = eth_usd_reporter

    assert r.gas_price_speed == "safeLow"

    r.gas_price_speed = "average"

    assert r.gas_price_speed != "safeLow"

    gas_price = await r.fetch_gas_price()

    assert isinstance(gas_price, int)
    assert gas_price > 0


@pytest.mark.asyncio
async def test_ethgasstation_error(eth_usd_reporter):
    async def no_gas_price(speed):
        return None

    r = eth_usd_reporter
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
    yield


@pytest.mark.asyncio
async def test_interval_reporter_submit_once(eth_usd_reporter):
    """Test reporting once to the TellorX playground on Rinkeby
    with three retries."""
    r = eth_usd_reporter

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
async def test_no_updated_value(eth_usd_reporter, bad_datasource):
    """Test handling for no updated value returned from datasource."""
    r = eth_usd_reporter

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
async def test_no_token_prices_for_profit_calc(eth_usd_reporter, bad_datasource, guaranteed_price_source):
    """Test handling for no token prices for profit calculation."""
    r = eth_usd_reporter

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
    yield


@pytest.mark.asyncio
async def test_handle_contract_master_read_timeout(eth_usd_reporter):
    """Test handling for contract master read timeout."""

    def conn_timeout(url, *args, **kwargs):
        raise asyncio.exceptions.TimeoutError()

    with mock.patch("web3.contract.ContractFunction.call", side_effect=conn_timeout):
        r = eth_usd_reporter
        r.fetch_gas_price = gas_price
        staked, status = await r.ensure_staked()

        assert not staked
        assert not status.ok
        assert "Unable to read reporters staker status" in status.error


@pytest.mark.asyncio
async def test_ensure_reporter_lock_check_after_submitval_attempt(
    monkeypatch, eth_usd_reporter, guaranteed_price_source
):
    r = eth_usd_reporter
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
