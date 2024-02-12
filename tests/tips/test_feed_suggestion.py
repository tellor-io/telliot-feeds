from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest
from brownie import chain
from hexbytes import HexBytes
from web3 import Web3

from telliot_feeds.datafeed import DataFeed
from telliot_feeds.feeds import matic_usd_median_feed
from telliot_feeds.queries.query_catalog import query_catalog
from telliot_feeds.reporters.tips.listener.assemble_call import AssembleCall
from telliot_feeds.reporters.tips.suggest_datafeed import get_feed_and_tip
from telliot_feeds.reporters.tips.tip_amount import fetch_feed_tip
from telliot_feeds.utils import log

log.DuplicateFilter.filter = lambda _, x: True


@pytest.mark.asyncio
async def test_no_tips(autopay_contract_setup, caplog):
    """Test no tips in autopay"""
    flex = await autopay_contract_setup
    await get_feed_and_tip(flex.autopay, skip_manual_feeds=False)
    assert "No one time tip funded queries available" in caplog.text
    assert "No funded feeds returned by autopay function call" in caplog.text
    assert "No tips available in autopay" in caplog.text


@pytest.mark.asyncio
async def test_funded_feeds_only(setup_datafeed, caplog):
    """Test feed tips but no one time tips and no reported timestamps"""
    flex = await setup_datafeed
    datafeed, tip = await get_feed_and_tip(flex.autopay, skip_manual_feeds=False)
    assert isinstance(datafeed, DataFeed)
    assert isinstance(tip, int)
    assert tip == int(1e18)
    assert "No one time tip funded queries available" in caplog.text


@pytest.mark.asyncio
async def test_one_time_tips_only(setup_one_time_tips, caplog):
    """Test one time tips but no feed tips"""
    flex = await setup_one_time_tips
    datafeed, tip = await get_feed_and_tip(flex.autopay, skip_manual_feeds=False)
    assert isinstance(datafeed, DataFeed)
    assert isinstance(tip, int)
    assert "No funded feeds returned by autopay function call" in caplog.text


@pytest.mark.asyncio
async def test_fetching_tips(tip_feeds_and_one_time_tips):
    """Test fetching tips when there are both feed tips and single tips
    A one time tip of 24 TRB exists autopay and plus 1 TRB in a feed
    its the highest so it should be the suggested query"""
    flex = await tip_feeds_and_one_time_tips
    datafeed, tip = await get_feed_and_tip(flex.autopay, skip_manual_feeds=False)
    assert isinstance(datafeed, DataFeed)
    assert isinstance(tip, int)
    assert tip == len(query_catalog._entries) * int(1e18)


@pytest.mark.asyncio
async def test_fake_queryid_feed_setup(autopay_contract_setup, caplog):
    """Test feed tips but no one time tips and no reported timestamps"""
    flex = await autopay_contract_setup
    query_data = "0x00000000000000000000000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000080000000000000000000000000000000000000000000000000000000000000000846616b655479706500000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000c0000000000000000000000000000000000000000000000000000000000000004000000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000003657468000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000037573640000000000000000000000000000000000000000000000000000000000"  # noqa: E501
    query_id = Web3.keccak(HexBytes(query_data))
    # setup a feed on autopay
    _, status = await flex.autopay.write(
        "setupDataFeed",
        gas_limit=3500000,
        legacy_gas_price=1,
        _queryId=query_id.hex(),
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
    datafeed, tip = await get_feed_and_tip(flex.autopay, skip_manual_feeds=False)
    assert datafeed is None
    assert tip is None
    assert "No funded feeds with telliot support found in autopay" in caplog.text


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
    tip_amount = await fetch_feed_tip(autopay=r.autopay, datafeed=matic_usd_median_feed)
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
    tip_amount = await fetch_feed_tip(autopay=r.autopay, datafeed=matic_usd_median_feed, timestamp=chain.time() + 2)
    assert tip_amount == int(1e18)
    with patch(
        "telliot_feeds.feeds.matic_usd_median_feed.source.fetch_new_datapoint",
        AsyncMock(side_effect=lambda: (None, None)),
    ):
        # tip amount should be 0 because the price threshold can't be calculated
        tip_amount = await fetch_feed_tip(autopay=r.autopay, datafeed=matic_usd_median_feed, timestamp=chain.time() + 2)
        assert tip_amount == 0
        assert (
            'Unable to fetch data from API for {"type":"SpotPrice","asset":"matic","currency":"usd"}, to check if price'
            " threshold is met" in caplog.text
        )


@pytest.mark.asyncio
async def test_feed_with_manual_source(autopay_contract_setup, caplog):
    """Test feed with threshold greater and a manual source"""
    r = await autopay_contract_setup
    query_data = "0x00000000000000000000000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000080000000000000000000000000000000000000000000000000000000000000000953706f745072696365000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000c000000000000000000000000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000080000000000000000000000000000000000000000000000000000000000000000466616b650000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000037573640000000000000000000000000000000000000000000000000000000000"  # noqa: E501
    query_id = Web3.keccak(HexBytes(query_data))
    # setup a feed on autopay
    _, status = await r.autopay.write(
        "setupDataFeed",
        gas_limit=3500000,
        legacy_gas_price=1,
        _queryId=query_id.hex(),
        _reward=1,
        _startTime=chain.time(),
        _interval=21600,
        _window=60,
        _priceThreshold=1,
        _rewardIncreasePerSecond=0,
        _queryData=query_data,
        _amount=int(10e18),
    )
    assert status.ok

    datafeed, tip = await get_feed_and_tip(r.autopay, skip_manual_feeds=False)
    assert datafeed.query.asset == "fake"
    assert datafeed.query.currency == "usd"
    assert datafeed.query.type == "SpotPrice"
    assert datafeed.source.type == "SpotPriceManualSource"
    assert tip == 1
    # submitting a value forces threshold check
    # since threshold check and this is a manual source feed shouldn't be suggested
    await r.oracle.write(
        "submitValue",
        _queryId=query_id,
        _queryData=query_data,
        _value=datafeed.query.value_type.encode(100.0),
        _nonce=0,
        gas_limit=3500000,
        legacy_gas_price=1,
    )
    chain.mine(timedelta=1)
    datafeed, tip = await get_feed_and_tip(r.autopay, skip_manual_feeds=False, current_timestamp=chain.time())
    assert datafeed is None
    assert tip is None
    assert "No auto source for feed with query type SpotPrice to check threshold" in caplog.text


@pytest.mark.asyncio
async def test_no_value_before(autopay_contract_setup, caplog):
    """Test for when there are no prior values when checking threshold"""
    r = await autopay_contract_setup
    query_id = matic_usd_median_feed.query.query_id.hex()
    query_data = matic_usd_median_feed.query.query_data.hex()
    _ = await r.autopay.write(
        "setupDataFeed",
        gas_limit=3500000,
        legacy_gas_price=1,
        _queryId=query_id,
        _reward=1,
        _startTime=chain.time(),
        _interval=21600,
        _window=1,
        _priceThreshold=1,
        _rewardIncreasePerSecond=0,
        _queryData=query_data,
        _amount=int(10e18),
    )
    # bypass window to force threshold check
    chain.mine(timedelta=1)
    # check that no feed is suggested since there is no value before and not in window
    feed, tip = await get_feed_and_tip(r.autopay, skip_manual_feeds=False, current_timestamp=chain.time())
    assert feed is not None
    assert tip is not None
    assert " No value before for SpotPrice" in caplog.text


@pytest.mark.asyncio
async def test_low_gas_limit_error(autopay_contract_setup, caplog):
    """Test ContractLogicError due to low multicall gas limit"""
    r = await autopay_contract_setup
    query_id = matic_usd_median_feed.query.query_id.hex()
    query_data = matic_usd_median_feed.query.query_data.hex()
    _ = await r.autopay.write(
        "setupDataFeed",
        gas_limit=3500000,
        legacy_gas_price=1,
        _queryId=query_id,
        _reward=1,
        _startTime=chain.time(),
        _interval=3600,
        _window=600,
        _priceThreshold=1,
        _rewardIncreasePerSecond=0,
        _queryData=query_data,
        _amount=int(10e18),
    )
    # advance chain
    chain.mine(timedelta=1)

    # imitate a low gas limit caused error
    with patch.object(AssembleCall, "gas_limit", 5000):
        suggestion = await get_feed_and_tip(r.autopay, skip_manual_feeds=False, current_timestamp=chain.time())
        assert suggestion == (None, None)
        assert "Error getting eligible funded feeds: multicall failed to fetch data: ContractLogicError" in caplog.text

    # should be no error when using default gas limit
    feed, tip_amount = await get_feed_and_tip(r.autopay, skip_manual_feeds=False, current_timestamp=chain.time())
    assert feed is not None
    assert tip_amount is not None


@pytest.mark.asyncio
async def test_skip_manual_feed(autopay_contract_setup, caplog):
    """Test feed tips when skip_manual_feeds is True"""
    flex = await autopay_contract_setup
    jai_usd_query_data = "0x00000000000000000000000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000080000000000000000000000000000000000000000000000000000000000000000953706f745072696365000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000c00000000000000000000000000000000000000000000000000000000000000040000000000000000000000000000000000000000000000000000000000000008000000000000000000000000000000000000000000000000000000000000000036a6169000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000037573640000000000000000000000000000000000000000000000000000000000"  # noqa: E501
    jai_usd_query_id = "0x8cad613ed5dbbcb23c028a6656cb051a1adf2954c8aaa4cb834b1e7e45069ca4"
    # setup a feed on autopay
    _, status = await flex.autopay.write(
        "setupDataFeed",
        gas_limit=3500000,
        legacy_gas_price=1,
        _queryId=jai_usd_query_id,
        _reward=1,
        _startTime=chain.time(),
        _interval=21600,
        _window=60,
        _priceThreshold=1,
        _rewardIncreasePerSecond=0,
        _queryData=jai_usd_query_data,
        _amount=int(1 * 10**18),
    )
    assert status.ok
    datafeed, tip = await get_feed_and_tip(flex.autopay, skip_manual_feeds=True)
    assert datafeed is None
    assert tip is None
    assert f"There is a tip for this query type: SpotPrice. Query data: {jai_usd_query_data[2:]}" in caplog.text
