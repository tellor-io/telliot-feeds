from contextlib import ExitStack
from unittest.mock import patch

import pytest

from telliot_feeds.feeds import eth_usd_median_feed
from telliot_feeds.reporters.customized.conditional_reporter import ConditionalReporter
from telliot_feeds.reporters.customized.conditional_reporter import GetDataBefore 
#from tests.utils.utils import chain_time


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
        stale_timeout =100,
        max_price_change=0.5,
        wait_period=0,
    )

r = await reporter
print(ConditionalReporter.get_tellor_latest_data(r))