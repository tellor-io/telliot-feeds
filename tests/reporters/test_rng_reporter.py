import time
from unittest.mock import patch

import pytest
import pytest_asyncio
from telliot_core.apps.core import TelliotCore
from telliot_core.utils.response import ResponseStatus
from web3.datastructures import AttributeDict

from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.tellor_rng import TellorRNG
from telliot_feeds.reporters.rng_interval import logger
from telliot_feeds.reporters.rng_interval import RNGReporter


# mock datasource failure
def mock_zero_timestamp():
    """Mock get_next_timestamp to return 0."""
    return 0


async def mock_response_status(*args, **kwargs):
    return ResponseStatus()


@pytest_asyncio.fixture(scope="function")
async def rng_reporter(mumbai_test_cfg, tellor_360):
    async with TelliotCore(config=mumbai_test_cfg) as core:
        contracts, account = tellor_360
        r = RNGReporter(
            oracle=contracts.oracle,
            token=contracts.token,
            autopay=contracts.autopay,
            endpoint=core.endpoint,
            account=account,
            chain_id=80001,
            transaction_type=0,
            min_native_token_balance=0,
        )

        return r


@pytest.mark.asyncio
async def test_report(rng_reporter):
    """Test reporting Tellor RNG value."""
    r = rng_reporter
    r.wait_period = 0

    EXPECTED_ERRORS = {
        "Current addess disputed. Switch address to continue reporting.",
        "Current address is locked in dispute or for withdrawal.",
        "Current address is in reporter lock.",
        "Estimated profitability below threshold.",
        "Estimated gas price is above maximum gas price.",
        "Unable to retrieve updated datafeed value.",
        "Unable to approve staking",
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
async def test_missing_blockhash(rng_reporter, monkeypatch, caplog):
    """Mock the datasource missing btc blockhash. Make sure still attemps to report after 3 retries."""
    r = rng_reporter
    r.wait_period = 0

    # mock datasource failure
    async def mock_no_val(*args, **kwargs):
        logger.warning("bazinga")
        return None, None

    with monkeypatch.context() as m:
        m.setattr("telliot_feeds.sources.blockhash_aggregator.TellorRNGManualSource.fetch_new_datapoint", mock_no_val)

        # mock functions that don't need to be tested here
        async def mock_ensure_staked(*args, **kwargs):
            return True, ResponseStatus()

        r.ensure_staked = mock_ensure_staked

        def has_native_token(*args, **kwargs):
            return True

        r.has_native_token = has_native_token

        async def mock_online(*args, **kwargs):
            return True

        r.is_online = mock_online

        r.check_reporter_lock = mock_response_status

        r.ensure_profitable = mock_response_status

        await r.report(report_count=3)

        assert caplog.text.count("bazinga") == 3


@pytest.mark.asyncio
async def test_invalid_timestamp(rng_reporter, monkeypatch, caplog):
    """Test reporting Tellor RNG value."""
    r = rng_reporter

    invalid_timestamp = 12345
    valid_timestamp = 1438269973
    with monkeypatch.context() as m:
        m.setattr("telliot_feeds.reporters.rng_interval.get_next_timestamp", mock_zero_timestamp)
        with patch(
            "telliot_feeds.sources.blockhash_aggregator.input_timeout",
            side_effect=[invalid_timestamp, valid_timestamp, "\n"],
        ):
            receipt, status = await r.report_once()
            assert status.ok
            assert receipt["status"] == 1
            assert "should be greater than eth genesis block timestamp" in caplog.text


@pytest.mark.asyncio
async def test_invalid_timestamp_in_future(rng_reporter, monkeypatch, caplog):
    """Test invalid timestamp in the future."""
    r = rng_reporter
    invalid_timestamp2 = int(time.time()) + 100000
    valid_timestamp = 1438269973
    with monkeypatch.context() as m:
        m.setattr("telliot_feeds.reporters.rng_interval.get_next_timestamp", mock_zero_timestamp)
        with patch(
            "telliot_feeds.sources.blockhash_aggregator.input_timeout",
            side_effect=[invalid_timestamp2, valid_timestamp, "\n"],
        ):
            receipt, status = await r.report_once()
            assert status.ok
            assert receipt["status"] == 1
            assert "less than current time" in caplog.text


def generate_numbers():
    current_number = 1678311000
    while current_number > 1678310000:
        yield current_number
        current_number = int(time.time())


@pytest.mark.asyncio
async def test_repeat_auto_rng_report_value(rng_reporter: RNGReporter, monkeypatch, caplog):
    """Test that shows the bad behavior before bug fix that was causing same value
    to be reported for timestamps that didn't have block hashes generated yet.
    Reason is global scope of local_source variable in assemble_rng_datafeed function
    """
    # function before fix was applied used local_source var from global scope
    from telliot_feeds.feeds.tellor_rng_feed import local_source

    async def assemble_feed(timestamp):
        local_source.set_timestamp(timestamp)
        return DataFeed(source=local_source, query=TellorRNG(timestamp=timestamp))

    rng_reporter.wait_period = 0
    num = generate_numbers()
    # test to show difference before fix
    with monkeypatch.context() as m:
        m.setattr("telliot_feeds.reporters.rng_interval.assemble_rng_datafeed", assemble_feed)
        m.setattr("telliot_feeds.reporters.rng_interval.get_next_timestamp", lambda: next(num))
        m.setattr(
            "telliot_feeds.reporters.rng_interval.RNGReporter.check_reporter_lock",
            mock_response_status,
        )
        # first report uses timestamp that has block hashes avaialble to generate rng
        # second timestamp does not have block hashes yet because it is current
        await rng_reporter.report(2)
        # encoded value for timestamp 1678311000
        count = caplog.text.count(
            "Reporter Encoded value: 236eabcc1c1dc5c01bd6357576b17e490eaf7aaa37b360485cddcd6877a395c3"
        )
        # count is 2 because second report uses same value
        assert count == 2


@pytest.mark.asyncio
async def test_unique_rng_report_value(rng_reporter: RNGReporter, monkeypatch, caplog):
    """Test that rng report value isn't submitting the same value twice."""
    rng_reporter.wait_period = 0
    num = generate_numbers()

    with monkeypatch.context() as m:
        m.setattr("telliot_feeds.reporters.rng_interval.get_next_timestamp", lambda: next(num))
        m.setattr(
            "telliot_feeds.reporters.rng_interval.RNGReporter.check_reporter_lock",
            mock_response_status,
        )
        await rng_reporter.report(2)
        count = caplog.text.count(
            "Reporter Encoded value: 236eabcc1c1dc5c01bd6357576b17e490eaf7aaa37b360485cddcd6877a395c3"
        )
        assert count == 1
