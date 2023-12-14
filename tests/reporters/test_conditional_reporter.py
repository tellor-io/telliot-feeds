from contextlib import ExitStack
from unittest.mock import patch

import pytest

from telliot_feeds.feeds import eth_usd_median_feed
from telliot_feeds.reporters.customized.conditional_reporter import ConditionalReporter
from telliot_feeds.reporters.customized.conditional_reporter import GetDataBefore
from tests.utils.utils import chain_time


@pytest.fixture(scope="function")
async def reporter(tellor_360, guaranteed_price_source):
    contracts, account = tellor_360
    feed = eth_usd_median_feed
    feed.source = guaranteed_price_source

    return ConditionalReporter(
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
        stale_timeout=100,
        max_price_change=0.5,
        wait_period=0,
    )


module = "telliot_feeds.reporters.customized.conditional_reporter."


@pytest.mark.asyncio
async def test_tellor_data_none(reporter, caplog):
    """Test when tellor data is None"""
    r = await reporter

    def patch_tellor_data_return(return_value):
        return patch(f"{module}ConditionalReporter.get_tellor_latest_data", return_value=return_value)

    with patch_tellor_data_return(None):
        await r.report(report_count=1)
        assert "tellor data returned None" in caplog.text

    with patch_tellor_data_return(GetDataBefore(False, b"", 0)):
        await r.report(report_count=1)
        assert "No oracle submissions in tellor for query" in caplog.text

    with patch_tellor_data_return(GetDataBefore(True, b"", 0)):
        await r.report(report_count=1)
        assert "tellor data is stale, time elapsed since last report" in caplog.text

