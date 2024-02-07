import pytest
from brownie import chain
from eth_utils import to_bytes
from web3 import Web3

from telliot_feeds.feeds.albt_usd_feed import albt_usd_median_feed
from telliot_feeds.reporters.tips.suggest_datafeed import get_feed_and_tip
from telliot_feeds.utils import log

# Turn off duplicate output filter
log.DuplicateFilter.filter = lambda _, x: True
query_data = "0x00000000000000000000000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000080000000000000000000000000000000000000000000000000000000000000000953706f745072696365000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000c0000000000000000000000000000000000000000000000000000000000000004000000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000004616c62740000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000037573640000000000000000000000000000000000000000000000000000000000"  # noqa: E501
query_id = Web3.keccak(to_bytes(hexstr=query_data)).hex()

txn_kwargs = {
    "gas_limit": 3500000,
    "legacy_gas_price": 1,
    "_queryId": query_id,
    "_queryData": query_data,
}
# setup a datafeed in autopay contact
data_feed = {
    "_reward": int(0.5 * 1e18),  # should run out after two in window submissions
    "_startTime": chain.time(),
    "_interval": 3600,
    "_window": 600,
    "_priceThreshold": 2500,
    "_rewardIncreasePerSecond": 0,
    "_amount": int(1 * 1e18),
}


@pytest.mark.asyncio
async def test_feed_suggestion(autopay_contract_setup, caplog):
    """Test the feed tip suggestions taking into account previous submissions"""
    flex = await autopay_contract_setup

    # setup and fund a feed on autopay
    _, _ = await flex.autopay.write(
        "setupDataFeed",
        **txn_kwargs,
        **data_feed,
    )
    # First report should get a funded query suggestion
    query, tip_amount = await get_feed_and_tip(
        autopay=flex.autopay, skip_manual_feeds=False, current_timestamp=chain.time()
    )
    assert query.get_state()["query"] == {"type": "SpotPrice", "asset": "albt", "currency": "usd"}
    assert tip_amount == int(0.5 * 1e18)
    get_price = await albt_usd_median_feed.source.fetch_new_datapoint()
    price = get_price[0]
    # First submission that is eligible for tip
    _, status = await flex.oracle.write(
        "submitValue",
        **txn_kwargs,
        _value=to_bytes(int(price * 1e18)).rjust(32, b"\0"),
        _nonce=0,
    )
    assert status.ok
    # Funded query shouldn't be suggested immediately after a report submission thats in window
    tip_amount = await get_feed_and_tip(
        autopay=flex.autopay, skip_manual_feeds=False, current_timestamp=chain.time() + 5
    )
    assert tip_amount == (None, None)
    assert "No tips available in autopay" in caplog.text
    # bypass time until next window
    chain.sleep(3600)
    query, tip_amount = await get_feed_and_tip(
        autopay=flex.autopay, skip_manual_feeds=False, current_timestamp=chain.time() + 5
    )
    assert query.get_state()["query"] == {"type": "SpotPrice", "asset": "albt", "currency": "usd"}
    assert tip_amount == int(0.5 * 1e18)
    chain.sleep(43200)
    # Second in window submission which should exhaust funds in feed
    _, status = await flex.oracle.write(
        "submitValue",
        **txn_kwargs,
        _value="0x" + (int(0.047841375 * 1e18)).to_bytes(32, byteorder="big").hex(),
        _nonce=0,
    )
    assert status.ok
    # Should be no tips available in autopay immediately after an in window report submission
    tip_amount = await get_feed_and_tip(
        autopay=flex.autopay, skip_manual_feeds=False, current_timestamp=chain.time() + 5
    )
    assert tip_amount == (None, None)
    # bypass time until next window
    chain.sleep(3600)
    # This feeds should no longer be suggested since two previous submissions exhausted the funds
    tip_amount = await get_feed_and_tip(
        autopay=flex.autopay, skip_manual_feeds=False, current_timestamp=chain.time() + 5
    )
    assert tip_amount == (None, None)


@pytest.mark.asyncio
async def test_one_time_tip_suggestion(autopay_contract_setup):
    """Test one time tip doesn't show after submission

    One time tipped query id shouldn't be suggested after they have already been submitted for once
    """
    flex = await autopay_contract_setup
    # Tip a query id
    await flex.autopay.write(
        "tip",
        **txn_kwargs,
        _amount=int(1e18),
    )
    # Feed suggestion should be tipped query id
    query, tip_amount = await get_feed_and_tip(
        autopay=flex.autopay, skip_manual_feeds=False, current_timestamp=chain.time()
    )
    assert query.get_state()["query"] == {"type": "SpotPrice", "asset": "albt", "currency": "usd"}
    assert tip_amount == 1e18
    _, status = await flex.oracle.write(
        "submitValue",
        **txn_kwargs,
        _value="0x" + (int(0.047841375 * 1e18)).to_bytes(32, byteorder="big").hex(),
        _nonce=0,
    )
    assert status.ok
    # One time tipped query id should no longer be suggested after a submission
    tip_amount = await get_feed_and_tip(autopay=flex.autopay, skip_manual_feeds=False, current_timestamp=chain.time())
    assert tip_amount == (None, None)
