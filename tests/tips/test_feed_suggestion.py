from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest
from brownie import chain
from eth_utils import to_bytes

from telliot_feeds.datafeed import DataFeed
from telliot_feeds.feeds import matic_usd_median_feed
from telliot_feeds.queries.query_catalog import query_catalog
from telliot_feeds.reporters.tips.suggest_datafeed import get_feed_and_tip
from telliot_feeds.reporters.tips.tip_amount import fetch_feed_tip
from telliot_feeds.utils import log

log.DuplicateFilter.filter = lambda _, x: True


@pytest.mark.asyncio
async def test_no_tips(autopay_contract_setup, caplog):
    """Test no tips in autopay"""
    flex = await autopay_contract_setup
    await get_feed_and_tip(flex.autopay)
    assert "No one time tip funded queries available" in caplog.text
    assert "No funded feeds returned by autopay function call" in caplog.text
    assert "No tips available in autopay" in caplog.text


@pytest.mark.asyncio
async def test_funded_feeds_only(setup_datafeed, caplog):
    """Test feed tips but no one time tips and no reported timestamps"""
    flex = await setup_datafeed
    datafeed, tip = await get_feed_and_tip(flex.autopay)
    assert isinstance(datafeed, DataFeed)
    assert isinstance(tip, int)
    assert tip == int(1e18)
    assert "No one time tip funded queries available" in caplog.text


@pytest.mark.asyncio
async def test_one_time_tips_only(setup_one_time_tips, caplog):
    """Test one time tips but no feed tips"""
    flex = await setup_one_time_tips
    datafeed, tip = await get_feed_and_tip(flex.autopay)
    assert isinstance(datafeed, DataFeed)
    assert isinstance(tip, int)
    assert "No funded feeds returned by autopay function call" in caplog.text


@pytest.mark.asyncio
async def test_fetching_tips(tip_feeds_and_one_time_tips):
    """Test fetching tips when there are both feed tips and single tips
    A one time tip of 24 TRB exists autopay and plus 1 TRB in a feed
    its the highest so it should be the suggested query"""
    flex = await tip_feeds_and_one_time_tips
    datafeed, tip = await get_feed_and_tip(flex.autopay)
    assert isinstance(datafeed, DataFeed)
    assert isinstance(tip, int)
    assert tip == len(query_catalog._entries) * int(1e18)


@pytest.mark.asyncio
async def test_fake_queryid_feed_setup(autopay_contract_setup, caplog):
    """Test feed tips but no one time tips and no reported timestamps"""
    flex = await autopay_contract_setup
    query_data = "0x00000000000000000000000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000080000000000000000000000000000000000000000000000000000000000000000953706f745072696365000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000002"  # noqa: E501
    query_id = flex.autopay.node._web3.keccak(to_bytes(hexstr=query_data)).hex()
    # setup a feed on autopay
    _, status = await flex.autopay.write(
        "setupDataFeed",
        gas_limit=3500000,
        legacy_gas_price=1,
        _queryId=query_id,
        _reward=1,
        _startTime=chain.time(),
        _interval=21600,
        _window=60,
        _priceThreshold=1,
        _rewardIncreasePerSecond=0,
        _queryData=query_data,
        _amount=int(1 * 10**18),
    )
    assert status.ok
    datafeed, tip = await get_feed_and_tip(flex.autopay)
    assert datafeed is None
    assert tip is None
    msg = (
        "No feeds to report, all funded feeds had threshold gt zero and "
        "no API support in telliot to check if threshold is met"
    )
    assert msg in caplog.text


@pytest.mark.asyncio
async def test_error_calculating_priceThreshold(autopay_contract_setup, caplog):
    """Test when there is an error calculating the priceThreshold"""
    r = await autopay_contract_setup
    price_threshold = 5
    # mock matic price
    price = 1.1054650000000001
    # setup and fund a feed on autopay
    query_id = matic_usd_median_feed.query.query_id
    _, _ = await r.autopay.write(
        "setupDataFeed",
        _reward=int(1e18),
        _startTime=chain.time(),
        _queryData=matic_usd_median_feed.query.query_data,
        _queryId=query_id,
        _interval=100,
        _window=99,
        _rewardIncreasePerSecond=0,
        _amount=int(5 * 10**18),
        _priceThreshold=price_threshold,
        gas_limit=3500000,
        legacy_gas_price=1,
    )
    tip_amount = await fetch_feed_tip(autopay=r.autopay, query_id=query_id)
    assert tip_amount == int(1e18)
    # report a price that meets the threshold
    current_price = price * (1 + price_threshold / 100)
    # report a price which would outside of window
    await r.oracle.write(
        "submitValue",
        _queryId=query_id,
        _queryData=matic_usd_median_feed.query.query_data,
        _value=matic_usd_median_feed.query.value_type.encode(current_price),
        _nonce=0,
        gas_limit=3500000,
        legacy_gas_price=1,
    )
    # there should be a tip since the price threshold is met and we're able to calculate the deviation
    tip_amount = await fetch_feed_tip(autopay=r.autopay, query_id=query_id, timestamp=chain.time() + 2)
    assert tip_amount == int(1e18)
    with patch(
        "telliot_feeds.feeds.matic_usd_median_feed.source.fetch_new_datapoint",
        AsyncMock(side_effect=lambda: (None, None)),
    ):
        # tip amount should be 0 because the price threshold can't be calculated
        tip_amount = await fetch_feed_tip(autopay=r.autopay, query_id=query_id, timestamp=chain.time() + 2)
        assert tip_amount == 0
        assert (
            'Unable to fetch data from API for {"type":"SpotPrice","asset":"matic","currency":"usd"}, to check if price'
            " threshold is met" in caplog.text
        )
