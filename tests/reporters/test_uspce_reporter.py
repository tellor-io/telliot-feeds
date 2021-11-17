import pytest

from telliot_feed_examples.feeds.uspce_feed import uspce_feed
from tests.conftest import reporter_submit_once


@pytest.mark.asyncio
async def test_uspce_interval_reporter_submit_once(rinkeby_cfg, master, oracle):
    """test report of uspce manual price"""
    await reporter_submit_once(rinkeby_cfg, master, oracle, uspce_feed)
