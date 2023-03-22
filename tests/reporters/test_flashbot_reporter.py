from unittest import mock

import pytest
import requests

from telliot_feeds.feeds.matic_usd_feed import matic_usd_median_feed
from telliot_feeds.reporters.flashbot import FlashbotsReporter


@pytest.mark.asyncio
async def test_http_error(tellor_360):
    """Test FlashbotsReporter HTTPError"""
    contracts, account = tellor_360
    account.unlock("")

    r = FlashbotsReporter(
        oracle=contracts.oracle,
        token=contracts.token,
        autopay=contracts.autopay,
        endpoint=contracts.oracle.node,
        account=account,
        signature_account=account,
        chain_id=5,
        transaction_type=0,
        min_native_token_balance=0,
        datafeed=matic_usd_median_feed,
        check_rewards=False,
    )

    with mock.patch("telliot_feeds.flashbots.provider.make_post_request", side_effect=requests.exceptions.HTTPError):
        res, status = await r.report_once()
        assert res is None
        assert not status.ok
