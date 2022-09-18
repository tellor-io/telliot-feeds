import pytest

from telliot_feeds.datafeed import DataFeed
from telliot_feeds.reporters.tips.suggest_datafeed import feed_suggestion
from telliot_feeds.utils import log

log.DuplicateFilter.filter = lambda _, x: True


@pytest.mark.asyncio
async def test_no_tips(autopay_contract_setup, caplog):
    """Test no tips in autopay"""
    autopay, _ = await autopay_contract_setup
    await feed_suggestion(autopay)
    assert "No one time tip funded queries available" in caplog.text
    assert "No funded feeds returned by autopay function call" in caplog.text
    assert "No tips available in autopay" in caplog.text


@pytest.mark.asyncio
async def test_funded_feeds_only(setup_datafeed, caplog):
    """Test feed tips but no one time tips and no reported timestamps"""
    datafeed, tip = await feed_suggestion(await setup_datafeed)
    assert isinstance(datafeed, DataFeed)
    assert isinstance(tip, int)
    assert "No one time tip funded queries available" in caplog.text


@pytest.mark.asyncio
async def test_one_time_tips_only(setup_one_time_tips, caplog):
    """Test one time tips but no feed tips"""
    datafeed, tip = await feed_suggestion(await setup_one_time_tips)
    assert isinstance(datafeed, DataFeed)
    assert isinstance(tip, int)
    assert "No funded feeds returned by autopay function call" in caplog.text


@pytest.mark.asyncio
async def test_fetching_tips(both_setup):
    """Test fetching tips when there are both feed tips and single tips
    A one time tip of 24 TRB exists autopay and plus 1 TRB in a feed
    its the highest so it should be the suggested query"""
    datafeed, tip = await feed_suggestion(await both_setup)
    assert isinstance(datafeed, DataFeed)
    assert isinstance(tip, int)
    assert tip == 25_000_000_000_000_000_000
