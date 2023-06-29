import datetime

import pytest

from telliot_feeds.feeds.landx_feed import corn
from telliot_feeds.reporters.tellor_360 import Tellor360Reporter
from telliot_feeds.sources.landx_source import LandXSource


@pytest.mark.asyncio
async def test_landx_source():
    price, date = await LandXSource(asset="corn").fetch_new_datapoint()
    assert isinstance(price, int)
    assert price > 0
    assert isinstance(date, datetime.datetime)


@pytest.mark.asyncio
async def test_landx_query_report(tellor_flex_reporter):
    r: Tellor360Reporter = tellor_flex_reporter
    r.datafeed = corn
    receipt, status = await r.report_once()
    assert status.ok
    assert receipt["status"] == 1
