import pytest

from telliot_feeds.datafeed import DataFeed
from telliot_feeds.reporters.tips.suggest_datafeed import feed_suggestion


@pytest.mark.asyncio
async def test_no_tips(autopay_contract_setup, caplog: pytest.LogCaptureFixture):
    """Test no tips in autopay"""
    await feed_suggestion(await autopay_contract_setup)
    assert "No one time tip funded queries available" in caplog.text
    assert "No funded feeds available" in caplog.text


@pytest.mark.asyncio
async def test_funded_feeds_only(setup_datafeed, caplog: pytest.LogCaptureFixture):
    """Test feed tips but no one time tips and no reported timestamps"""
    res = await feed_suggestion(await setup_datafeed)
    assert isinstance(res, tuple)
    assert isinstance(res[0], DataFeed)
    assert isinstance(res[1], int)
    assert len(res) == 2
    assert "No submission reports for all query ids" in caplog.text


@pytest.mark.asyncio
async def test_one_time_tips_only(setup_one_time_tips, caplog: pytest.LogCaptureFixture):
    """Test one time tips but no feed tips"""
    res = await feed_suggestion(await setup_one_time_tips)
    assert len(res) == 2
    assert isinstance(res, tuple)
    assert isinstance(res[0], DataFeed)
    assert isinstance(res[1], int)
    assert "No funded feeds available in autopay!" in caplog.text


@pytest.mark.asyncio
async def test_fetching_tips(both_setup, caplog: pytest.LogCaptureFixture):
    """Test fetching tips when there are both feed tips and single tips
    A one time tip of 24 TRB exists autopay and plus 1 TRB in a feed
    its the highest so it should be the suggested query"""
    res = await feed_suggestion(await both_setup)
    assert len(res) == 2
    assert isinstance(res, tuple)
    assert isinstance(res[0], DataFeed)
    assert isinstance(res[1], int)
    assert res[1] == 25_000_000_000_000_000_000
