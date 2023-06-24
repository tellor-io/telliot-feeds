from contextlib import ExitStack
from unittest.mock import patch

import pytest

from telliot_feeds.feeds import eth_usd_median_feed
from telliot_feeds.reporters.customized import ChainLinkFeeds
from telliot_feeds.reporters.customized.backup_reporter import ChainlinkBackupReporter
from telliot_feeds.reporters.customized.backup_reporter import GetDataBefore
from telliot_feeds.reporters.customized.backup_reporter import RoundData
from tests.utils.utils import chain_time


@pytest.fixture(scope="function")
async def reporter(tellor_360, guaranteed_price_source):
    contracts, account = tellor_360
    feed = eth_usd_median_feed
    feed.source = guaranteed_price_source

    return ChainlinkBackupReporter(
        oracle=contracts.oracle,
        token=contracts.token,
        autopay=contracts.autopay,
        endpoint=contracts.oracle.node,
        account=account,
        chain_id=80001,
        transaction_type=0,
        min_native_token_balance=0,
        datafeed=feed,
        check_rewards=False,
        chainlink_is_frozen_timeout=100,
        chainlink_max_price_change=0.5,
        chainlink_feed=ChainLinkFeeds[80001],
        wait_period=0,
    )


module = "telliot_feeds.reporters.customized.backup_reporter."


@pytest.mark.asyncio
async def test_recent_link_data(reporter, chain, caplog):
    r = await reporter

    with ExitStack() as stack:
        stack.enter_context(patch(f"{module}current_time", new=lambda: chain_time(chain)))
        stack.enter_context(
            patch(
                f"{module}ChainlinkBackupReporter.get_chainlink_latest_round_data",
                return_value=RoundData(2, 1, chain_time(chain), chain_time(chain), 2),
            )
        )
        stack.enter_context(
            patch(
                f"{module}ChainlinkBackupReporter.get_chainlink_previous_round_data",
                return_value=RoundData(1, 1, chain_time(chain), chain_time(chain), 1),
            )
        )
        await r.report(report_count=1)
        assert 'chainLink {"type":"SpotPrice","asset":"eth","currency":"usd"} data is recent enough' in caplog.text


@pytest.mark.asyncio
async def test_frozen_data(reporter, chain, caplog):
    r = await reporter
    old_timestamp = chain_time(chain) - 1000
    with ExitStack() as stack:
        stack.enter_context(patch(f"{module}current_time", new=lambda: chain_time(chain)))
        stack.enter_context(
            patch(
                f"{module}ChainlinkBackupReporter.get_chainlink_latest_round_data",
                return_value=RoundData(1, 1, old_timestamp, old_timestamp, 1),
            )
        )
        await r.report(report_count=1)
        assert "chainlink is almost frozen" in caplog.text
        assert "Sending submitValue transaction" in caplog.text


@pytest.mark.asyncio
async def test_tellor_data_exists(reporter, chain, caplog):
    r = await reporter
    # submit tellor data to oracle
    await r.report(report_count=1)
    chain.mine(1, timedelta=1)
    with ExitStack() as stack:
        stack.enter_context(patch(f"{module}current_time", new=lambda: chain_time(chain)))
        stack.enter_context(
            patch(
                f"{module}ChainlinkBackupReporter.get_chainlink_latest_round_data",
                return_value=RoundData(1, 1, 1234, 1234, 1),
            )
        )
        await r.report(report_count=1)
        assert 'tellor {"type":"SpotPrice","asset":"eth","currency":"usd"} data is recent enough' in caplog.text


@pytest.mark.asyncio
async def test_price_change_condition(reporter, chain, caplog):
    r = await reporter
    latest_round_data = RoundData(2, 3, chain_time(chain), chain_time(chain), 2)
    # price deviation over 50%
    previous_round_data = RoundData(1, 1, chain_time(chain), chain_time(chain), 1)
    chain.mine(1, timedelta=1)
    with ExitStack() as stack:
        stack.enter_context(patch(f"{module}current_time", new=lambda: chain_time(chain)))
        stack.enter_context(
            patch(f"{module}ChainlinkBackupReporter.get_chainlink_latest_round_data", return_value=latest_round_data)
        )
        stack.enter_context(
            patch(
                f"{module}ChainlinkBackupReporter.get_chainlink_previous_round_data", return_value=previous_round_data
            )
        )
        await r.report(report_count=1)
        assert "chainlink price change above max" in caplog.text
        assert "Sending submitValue transaction" in caplog.text


@pytest.mark.asyncio
async def test_tellor_data_none(reporter, caplog):
    """Test when tellor data is None"""
    r = await reporter

    def patch_tellor_data_return(return_value):
        return patch(f"{module}ChainlinkBackupReporter.get_tellor_latest_data", return_value=return_value)

    with patch_tellor_data_return(None):
        await r.report(report_count=1)
        assert "tellor data returned None" in caplog.text

    with patch_tellor_data_return(GetDataBefore(False, b"", 0)):
        await r.report(report_count=1)
        assert "No oracle submissions in tellor for query" in caplog.text

    with patch_tellor_data_return(GetDataBefore(True, b"", 0)):
        await r.report(report_count=1)
        assert "tellor data is stale, time elapsed since last report" in caplog.text


@pytest.mark.asyncio
async def test_bad_chainlink_address_msg(reporter, caplog):
    """Test when chainlink address is not valid"""
    r = await reporter
    bad_address = "0x5f4eC3Df9cbd43714FE2740f5E3616155c5b8419"
    r.chainlink_feed = bad_address
    await r.report(report_count=1)
    assert f"Make sure you're using the correct chainlink feed address {bad_address}" in caplog.text
