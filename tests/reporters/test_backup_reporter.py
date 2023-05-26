from contextlib import ExitStack
from unittest.mock import patch

import pytest

from telliot_feeds.feeds import eth_usd_median_feed
from telliot_feeds.reporters.customized.backup_reporter import BackupReporter
from telliot_feeds.reporters.customized.backup_reporter import RoundData


def chain_time(chain):
    return round(chain.time())


@pytest.fixture(scope="function")
async def reporter(tellor_360, guaranteed_price_source, mock_flex_contract, mock_token_contract):
    contracts, account = tellor_360
    feed = eth_usd_median_feed
    feed.source = guaranteed_price_source

    return BackupReporter(
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
        chainlink_max_price_deviation=0.5,
        wait_period=0,
    )


module = "telliot_feeds.reporters.customized.backup_reporter.BackupReporter."


@pytest.mark.asyncio
async def test_recent_link_data(reporter, chain, caplog):
    r = await reporter

    with ExitStack() as stack:
        stack.enter_context(patch(f"{module}current_time", new=lambda _: chain_time(chain)))
        stack.enter_context(
            patch(
                f"{module}get_chainlink_latest_round_data",
                return_value=RoundData(2, 1, chain_time(chain), chain_time(chain), 2),
            )
        )
        stack.enter_context(
            patch(
                f"{module}get_chainlink_previous_round_data",
                return_value=RoundData(1, 1, chain_time(chain), chain_time(chain), 1),
            )
        )
        await r.report(report_count=1)
        assert "chainLink ETH/USD data is recent enough" in caplog.text


@pytest.mark.asyncio
async def test_frozen_data(reporter, chain, caplog):
    r = await reporter
    old_timestamp = chain_time(chain) - 1000
    with ExitStack() as stack:
        stack.enter_context(patch(f"{module}current_time", new=lambda _: chain_time(chain)))
        stack.enter_context(
            patch(
                f"{module}get_chainlink_latest_round_data",
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
        stack.enter_context(patch(f"{module}current_time", new=lambda _: round(chain.time())))
        stack.enter_context(
            patch(
                f"{module}get_chainlink_latest_round_data",
                return_value=RoundData(1, 1, round(chain.time()), round(chain.time()), 1),
            )
        )
        await r.report(report_count=1)
        assert "tellor ETH/USD data is recent enough" in caplog.text


@pytest.mark.asyncio
async def test_price_deviation_condition(reporter, chain, caplog):
    r = await reporter
    latest_round_data = RoundData(2, 3, chain_time(chain), chain_time(chain), 2)
    # price deviation over 50%
    previous_round_data = RoundData(1, 1, chain_time(chain), chain_time(chain), 1)
    chain.mine(1, timedelta=1)
    with ExitStack() as stack:
        stack.enter_context(patch(f"{module}current_time", new=lambda _: chain_time(chain)))
        stack.enter_context(patch(f"{module}get_chainlink_latest_round_data", return_value=latest_round_data))
        stack.enter_context(patch(f"{module}get_chainlink_previous_round_data", return_value=previous_round_data))
        await r.report(report_count=1)
        assert "chainlink price change above max" in caplog.text
        assert "Sending submitValue transaction" in caplog.text
