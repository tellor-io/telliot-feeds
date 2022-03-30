"""
Tests covering the IntervalReporter class from
telliot's reporters subpackage.
"""
from datetime import datetime
from typing import Any

import pytest
from telliot_core.apps.core import TelliotCore
from telliot_core.datafeed import DataFeed
from telliot_core.gas.etherscan_gas import EtherscanGasPrice
from telliot_core.utils.response import ResponseStatus
from web3.datastructures import AttributeDict

from telliot_feed_examples.feeds.eth_usd_feed import eth_usd_median_feed
from telliot_feed_examples.reporters.interval import IntervalReporter


@pytest.fixture
async def eth_usd_reporter(rinkeby_cfg):
    """Returns an instance of an IntervalReporter using
    the ETH/USD median datafeed."""
    async with TelliotCore(config=rinkeby_cfg) as core:
        account = core.get_account()
        tellorx = core.get_tellorx_contracts()
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
        return r


@pytest.mark.asyncio
async def test_fetch_datafeed(eth_usd_reporter):
    r = eth_usd_reporter
    feed = await r.fetch_datafeed()
    assert isinstance(feed, DataFeed)

    r.datafeed = None
    assert r.datafeed is None
    feed = await r.fetch_datafeed()
    assert isinstance(feed, DataFeed)


@pytest.mark.skip(
    "Skipping because the error is from telliot-core and not from the reporter."
)
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


@pytest.mark.skip("Asks for psswd")
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

    ORACLE_ADDRESSES = {
        "0xe8218cACb0a5421BC6409e498d9f8CC8869945ea",  # mainnet
        "0x18431fd88adF138e8b979A7246eb58EA7126ea16",  # rinkeby
    }

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


@pytest.mark.skip("Asks for psswd")
@pytest.mark.asyncio
async def test_no_updated_value(eth_usd_reporter, bad_source):
    """Test handling for no updated value returned from datasource."""
    r = eth_usd_reporter

    # Clear latest datapoint
    r.datafeed.source._history.clear()

    # Replace PriceAggregator's sources with test source that
    # returns no updated DataPoint
    r.datafeed.source.sources = [bad_source]

    # Override reporter lock status
    async def passing():
        return ResponseStatus()

    r.check_reporter_lock = passing

    # Override reporter profit check
    async def profit(datafeed: DataFeed[Any]):
        return ResponseStatus()

    r.ensure_profitable = profit

    tx_receipt, status = await r.report_once()

    assert not tx_receipt
    assert not status.ok
    assert status.error == "Unable to retrieve updated datafeed value."
