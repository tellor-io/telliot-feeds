import pytest

from brownie import chain
from eth_utils import to_bytes

from telliot_feeds.feeds import CATALOG_FEEDS
from telliot_feeds.reporters.tips import CATALOG_QUERY_IDS
from telliot_feeds.reporters.tips import CATALOG_QUERY_DATA
from telliot_feeds.reporters.tips.selected_queryid.tip_amount import fetch_feed_tip

from telliot_core.utils.timestamp import TimeStamp

@pytest.mark.asyncio
async def test_single_feed(autopay_contract_setup):
    """Test price threshold == 0"""
    contract, _ = await autopay_contract_setup
    query_id, query_data = list(zip(CATALOG_QUERY_IDS, CATALOG_QUERY_DATA))[7]
    reward = 1 * 10**18
    start_time = TimeStamp.now().ts
    interval = 100
    window = 99
    price_threshold = 0

    # setup and fund a feed on autopay
    _, _ = await contract.write(
        "setupDataFeed",
        gas_limit=3500000,
        legacy_gas_price=1,
        _queryId=query_id,
        _reward=reward,
        _startTime=start_time,
        _interval=interval,
        _window=window,
        _priceThreshold=price_threshold,
        _rewardIncreasePerSecond=0,
        _queryData=query_data,
        _amount=int(5 * 10**18),
    )
    tip_amount = await fetch_feed_tip(autopay=contract, query_id=query_id)
    assert tip_amount == reward

@pytest.mark.asyncio
async def test_priceThreshold_gt_zero(autopay_contract_setup):
    """Test price threshold > 0 and not first in window"""
    contract, oracle = await autopay_contract_setup
    query_id, query_data = list(zip(CATALOG_QUERY_IDS, CATALOG_QUERY_DATA))[7]
    tag = CATALOG_QUERY_IDS[query_id]
    reward = 1 * 10**18
    interval = 100
    window = 99
    price_threshold = int(1e18)

    # setup and fund a feed on autopay
    _, _ = await contract.write(
        "setupDataFeed",
        gas_limit=3500000,
        legacy_gas_price=1,
        _queryId=query_id,
        _reward=reward,
        _startTime=chain.time(),
        _interval=interval,
        _window=window,
        _priceThreshold=price_threshold,
        _rewardIncreasePerSecond=0,
        _queryData=query_data,
        _amount=int(5 * 10**18),
    )
    get_price = await CATALOG_FEEDS[tag].source.fetch_new_datapoint()
    price = get_price[0]
    tip_amount = await fetch_feed_tip(autopay=contract, query_id=query_id)
    assert tip_amount == reward
    await oracle.write(
        "submitValue",
        gas_limit=3500000,
        legacy_gas_price=1,
        _queryId=query_id,
        _value=to_bytes(int(price*1e18)).rjust(32, b'\0'),
        _nonce=0,
        _queryData=query_data,
    )
    tip_amount = await fetch_feed_tip(autopay=contract, query_id=query_id, timestamp=chain.time() + 1)
    assert tip_amount == 0

@pytest.mark.asyncio
async def test_ousideof_window_pt0(autopay_contract_setup):
    """Test price threshold == 0 outside of window"""
    contract, _ = await autopay_contract_setup
    query_id, query_data = list(zip(CATALOG_QUERY_IDS, CATALOG_QUERY_DATA))[7]
    reward = 1 * 10**18
    start_time = TimeStamp.now().ts
    interval = 10
    window = 1
    price_threshold = 0

    # setup and fund a feed on autopay
    _, _ = await contract.write(
        "setupDataFeed",
        gas_limit=3500000,
        legacy_gas_price=1,
        _queryId=query_id,
        _reward=reward,
        _startTime=start_time,
        _interval=interval,
        _window=window,
        _priceThreshold=price_threshold,
        _rewardIncreasePerSecond=0,
        _queryData=query_data,
        _amount=int(5 * 10**18),
    )
    tip_amount = await fetch_feed_tip(autopay=contract, query_id=query_id)
    assert tip_amount == 0

@pytest.mark.asyncio
async def test_priceThreshold_zero(autopay_contract_setup):
    """Test price threshold = 0 and not first in window"""
    contract, oracle = await autopay_contract_setup
    query_id, query_data = list(zip(CATALOG_QUERY_IDS, CATALOG_QUERY_DATA))[7]
    tag = CATALOG_QUERY_IDS[query_id]
    reward = 1 * 10**18
    interval = 100
    window = 99
    price_threshold = 0

    # setup and fund a feed on autopay
    _, _ = await contract.write(
        "setupDataFeed",
        gas_limit=3500000,
        legacy_gas_price=1,
        _queryId=query_id,
        _reward=reward,
        _startTime=chain.time(),
        _interval=interval,
        _window=window,
        _priceThreshold=price_threshold,
        _rewardIncreasePerSecond=0,
        _queryData=query_data,
        _amount=int(5 * 10**18),
    )
    tip_amount = await fetch_feed_tip(autopay=contract, query_id=query_id)
    assert tip_amount == reward
    await oracle.write(
        "submitValue",
        gas_limit=3500000,
        legacy_gas_price=1,
        _queryId=query_id,
        _value=to_bytes(int(10*1e18)).rjust(32, b'\0'),
        _nonce=0,
        _queryData=query_data,
    )
    tip_amount = await fetch_feed_tip(autopay=contract, query_id=query_id, timestamp=chain.time() + 1)
    assert tip_amount == 0

@pytest.mark.asyncio
async def test_meet_priceThreshold(autopay_contract_setup):
    """Test price threshold > 0 and not first in window but meets threshold"""
    contract, oracle = await autopay_contract_setup
    query_id, query_data = list(zip(CATALOG_QUERY_IDS, CATALOG_QUERY_DATA))[7]
    tag = CATALOG_QUERY_IDS[query_id]
    reward = 1 * 10**18
    interval = 100
    window = 99
    price_threshold = 1

    # setup and fund a feed on autopay
    _, status = await contract.write(
        "setupDataFeed",
        gas_limit=3500000,
        legacy_gas_price=1,
        _queryId=query_id,
        _reward=reward,
        _startTime=chain.time(),
        _interval=interval,
        _window=window,
        _priceThreshold=price_threshold,
        _rewardIncreasePerSecond=0,
        _queryData=query_data,
        _amount=int(5 * 10**18),
    )
    tip_amount = await fetch_feed_tip(autopay=contract, query_id=query_id)
    assert tip_amount == reward
    get_price = await CATALOG_FEEDS[tag].source.fetch_new_datapoint()
    price = get_price[0]
    await oracle.write(
        "submitValue",
        gas_limit=3500000,
        legacy_gas_price=1,
        _queryId=query_id,
        _value=to_bytes(int(price*1e18)).rjust(32, b'\0'),
        _nonce=0,
        _queryData=query_data,
    )
    tip_amount = await fetch_feed_tip(autopay=contract, query_id=query_id, timestamp=chain.time() + 1)
    assert tip_amount == reward