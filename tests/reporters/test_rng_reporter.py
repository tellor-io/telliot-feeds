import time
from unittest.mock import patch

import pytest
import pytest_asyncio
from telliot_core.apps.core import TelliotCore
from telliot_core.utils.response import ResponseStatus
from web3.datastructures import AttributeDict

from telliot_feeds.reporters.rng_interval import logger
from telliot_feeds.reporters.rng_interval import RNGReporter


# mock datasource failure
def mock_zero_timestamp():
    """Mock get_next_timestamp to return 0."""
    return 0


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

    monkeypatch.setattr(
        "telliot_feeds.sources.blockhash_aggregator.TellorRNGManualSource.fetch_new_datapoint", mock_no_val
    )

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

    async def mock_check_reporter_lock(*args, **kwargs):
        return ResponseStatus()

    r.check_reporter_lock = mock_check_reporter_lock

    async def mock_ensure_profitable(*args, **kwargs):
        return ResponseStatus()

    r.ensure_profitable = mock_ensure_profitable

    await r.report(report_count=3)

    assert caplog.text.count("bazinga") == 3


@pytest.mark.asyncio
async def test_invalid_timestamp(rng_reporter, monkeypatch, caplog):
    """Test reporting Tellor RNG value."""
    r = rng_reporter

    invalid_timestamp = 12345
    valid_timestamp = 1438269973
    monkeypatch.setattr("telliot_feeds.reporters.rng_interval.get_next_timestamp", mock_zero_timestamp)
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
    monkeypatch.setattr("telliot_feeds.reporters.rng_interval.get_next_timestamp", mock_zero_timestamp)
    with patch(
        "telliot_feeds.sources.blockhash_aggregator.input_timeout",
        side_effect=[invalid_timestamp2, valid_timestamp, "\n"],
    ):
        receipt, status = await r.report_once()
        assert status.ok
        assert receipt["status"] == 1
        assert "less than current time" in caplog.text
