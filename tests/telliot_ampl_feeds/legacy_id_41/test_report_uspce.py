import pytest

from telliot_ampl_feeds.feeds.uspce import uspce_feed
from tests.conftest import reporter_submit_once


@pytest.mark.asyncio
async def test_uspce_interval_reporter_submit_once(cfg, master, oracle):
    """test report of uspce manual price"""
    reporter_submit_once(cfg, master, oracle, uspce_feed)
