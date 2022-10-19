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
from brownie import Reporter
from telliot_core.apps.core import ChainedAccount
from telliot_core.apps.core import Contract
from telliot_core.apps.core import find_accounts
from telliot_core.apps.core import TelliotCore
from telliot_core.gas.legacy_gas import ethgasstation
from telliot_core.utils.response import ResponseStatus
from web3.datastructures import AttributeDict

from telliot_feeds.datafeed import DataFeed
from telliot_feeds.feeds.eth_usd_feed import eth_usd_median_feed
from telliot_feeds.reporters import interval
from telliot_feeds.reporters.custom_reporter import CustomXReporter
from telliot_feeds.sources.etherscan_gas import EtherscanGasPrice
from tests.utils.utils import gas_price
from tests.utils.utils import passing_bool_w_status
from tests.utils.utils import passing_status


account_fake = accounts.add("023861e2ceee1ea600e43cbd203e9e01ea2ed059ee3326155453a1ed3b1113a9")
try:
    account = find_accounts(name="fake_custom_reporter_address", chain_id=4)[0]
except IndexError:
    account = ChainedAccount.add(
        name="fake_custom_reporter_address",
        chains=4,
        key="023861e2ceee1ea600e43cbd203e9e01ea2ed059ee3326155453a1ed3b1113a9",
        password="",
    )


@pytest.fixture
def mock_reporter_contract(tellorx_master_mock_contract, tellorx_oracle_mock_contract):
    """mock custom reporter contract"""
    return account_fake.deploy(
        Reporter,
        tellorx_master_mock_contract.address,
        tellorx_oracle_mock_contract.address,
        0,
    )


@pytest_asyncio.fixture(scope="function")
async def custom_reporter(
    rinkeby_test_cfg,
    tellorx_master_mock_contract,
    tellorx_oracle_mock_contract,
    mock_reporter_contract,
):
    """Returns an instance of an CustomReporter using
    the ETH/USD median datafeed."""
    async with TelliotCore(config=rinkeby_test_cfg) as core:
        custom_contract = Contract(mock_reporter_contract.address, mock_reporter_contract.abi, core.endpoint, account)
        custom_contract.connect()
        tellorx = core.get_tellorx_contracts()
        tellorx.master.address = tellorx_master_mock_contract.address
        tellorx.oracle.address = tellorx_oracle_mock_contract.address
        tellorx.master.connect()
        tellorx.oracle.connect()
        r = CustomXReporter(
            custom_contract=custom_contract,
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


@pytest.mark.asyncio
async def test_interval_reporter_submit_once(custom_reporter):
    """Test reporting once to  TellorX through custom contract
    with three retries."""
    r = custom_reporter

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

    oracle_address = r.custom_contract.address
    tx_receipt, status = await r.report_once()
    # Reporter submitted
    if tx_receipt is not None and status.ok:
        assert isinstance(tx_receipt, AttributeDict)
        assert tx_receipt.to in oracle_address
    # Reporter did not submit
    else:
        assert not tx_receipt
        assert not status.ok
        assert status.error in EXPECTED_ERRORS


@pytest.mark.asyncio
async def test_fetch_datafeed(custom_reporter):
    r = custom_reporter
    feed = await r.fetch_datafeed()
    assert isinstance(feed, DataFeed)

    r.datafeed = None
    assert r.datafeed is None
    feed = await r.fetch_datafeed()
    assert isinstance(feed, DataFeed)


@pytest.mark.asyncio
async def test_get_fee_info(custom_reporter):
    info, time = await custom_reporter.get_fee_info()

    assert isinstance(time, datetime)
    assert isinstance(info, EtherscanGasPrice)
    assert isinstance(info.LastBlock, int)
    assert info.LastBlock > 0
    assert isinstance(info.gasUsedRatio, list)


@pytest.mark.asyncio
async def test_get_num_reports_by_id(custom_reporter):
    r = custom_reporter
    num, status = await r.get_num_reports_by_id(r.datafeed.query.query_id)

    assert isinstance(status, ResponseStatus)

    if status.ok:
        assert isinstance(num, int)
    else:
        assert num is None


@pytest.mark.asyncio
async def test_ensure_staked(custom_reporter):
    """Test staking status of reporter."""
    staked, status = await custom_reporter.ensure_staked()
    assert staked
    assert status.ok


@pytest.mark.asyncio
async def test_check_reporter_lock(custom_reporter):
    """Test checking if in reporter lock."""
    r = custom_reporter
    r.last_submission_timestamp = 0

    status = await r.check_reporter_lock()

    assert isinstance(status, ResponseStatus)
    if not status.ok:
        assert status.error == "Current address is in reporter lock."
        assert r.last_submission_timestamp != 0


@pytest.mark.asyncio
async def test_ensure_profitable(custom_reporter):
    """Test profitability check."""
    r = custom_reporter

    assert r.expected_profit == "YOLO"

    status = await r.ensure_profitable(r.datafeed)

    assert status.ok

    r.expected_profit = 1e10
    status = await r.ensure_profitable(r.datafeed)

    assert not status.ok
    assert status.error == "Estimated profitability below threshold."


@pytest.mark.asyncio
async def test_fetch_gas_price(custom_reporter):
    """Test retrieving custom gas price from eth gas station."""
    r = custom_reporter

    assert r.gas_price_speed == "safeLow"

    r.gas_price_speed = "average"

    assert r.gas_price_speed != "safeLow"

    gas_price = await r.fetch_gas_price()

    assert isinstance(gas_price, int)
    assert gas_price > 0


@pytest.mark.asyncio
async def test_ethgasstation_error(custom_reporter):
    async def no_gas_price(speed):
        return None

    r = custom_reporter
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
async def test_no_updated_value(custom_reporter, bad_datasource):
    """Test handling for no updated value returned from datasource."""
    r = custom_reporter

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
    assert status.error == "Unable to retrieve updated datafeed value."


@pytest.mark.asyncio
async def test_no_token_prices_for_profit_calc(custom_reporter, bad_datasource, guaranteed_price_source):
    """Test handling for no token prices for profit calculation."""
    r = custom_reporter

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
async def test_handle_contract_master_read_timeout(custom_reporter):
    """Test handling for contract master read timeout."""

    def conn_timeout(url, *args, **kwargs):
        raise asyncio.exceptions.TimeoutError()

    with mock.patch("web3.contract.ContractFunction.call", side_effect=conn_timeout):
        r = custom_reporter
        r.fetch_gas_price = gas_price
        staked, status = await r.ensure_staked()

        assert not staked
        assert not status.ok
        assert "Unable to read reporters staker status" in status.error


@pytest.mark.asyncio
async def test_ensure_reporter_lock_check_after_submitval_attempt(
    monkeypatch, custom_reporter, guaranteed_price_source
):
    r = custom_reporter
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
