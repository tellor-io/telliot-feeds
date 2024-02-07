from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest
from brownie import chain
from eth_abi import encode_abi
from hexbytes import HexBytes
from web3 import Web3

from telliot_feeds.cli.utils import build_feed_from_input
from telliot_feeds.dtypes.datapoint import datetime_now_utc
from telliot_feeds.feeds import DATAFEED_BUILDER_MAPPING
from telliot_feeds.reporters.tips.suggest_datafeed import get_feed_and_tip
from telliot_feeds.reporters.tips.tip_amount import fetch_feed_tip


@pytest.mark.asyncio
async def test_mashup_type(autopay_contract_setup, caplog):
    """Test query type existing query type MimicryMacroMarketMashupbut with query id not in catalog
    and listening for tips without selecting a query id in the cli
    """
    r = await autopay_contract_setup
    query_id = "0x0c70e0b36b9849038027617c0e2ef87ac8c3f0e68168faf5186e0981b6c5eb47"
    query_data = "0x0000000000000000000000000000000000000000000000000000000000000040000000000000000000000000000000000000000000000000000000000000008000000000000000000000000000000000000000000000000000000000000000184d696d696372794d6163726f4d61726b65744d6173687570000000000000000000000000000000000000000000000000000000000000000000000000000006c0000000000000000000000000000000000000000000000000000000000000008000000000000000000000000000000000000000000000000000000000000000c0000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000003a0000000000000000000000000000000000000000000000000000000000000000a6d61726b65742d636170000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000003757364000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000040000000000000000000000000000000000000000000000000000000000000080000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000001800000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000004000000000000000000000000050f5474724e0ee42d9a4e711ccfb275809fd6d4a0000000000000000000000000000000000000000000000000000000000000010657468657265756d2d6d61696e6e6574000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000040000000000000000000000000f87e31492faf9a91b02ee0deaad50d51d56d5d4d0000000000000000000000000000000000000000000000000000000000000010657468657265756d2d6d61696e6e657400000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000004000000000000000000000000034d85c9cdeb23fa97cb08333b511ac86e1c4e2580000000000000000000000000000000000000000000000000000000000000010657468657265756d2d6d61696e6e6574000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000040000000000000000000000000790b2cf29ed4f310bf7641f013c65d4560d283710000000000000000000000000000000000000000000000000000000000000010657468657265756d2d6d61696e6e6574000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000003000000000000000000000000000000000000000000000000000000000000006000000000000000000000000000000000000000000000000000000000000001400000000000000000000000000000000000000000000000000000000000000220000000000000000000000000000000000000000000000000000000000000006000000000000000000000000000000000000000000000000000000000000000a00000000000000000000000003845badade8e6dff049820680d1f14bd3903a5d00000000000000000000000000000000000000000000000000000000000000010657468657265756d2d6d61696e6e657400000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000473616e6400000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000006000000000000000000000000000000000000000000000000000000000000000a00000000000000000000000000f5d2fb29fb7d3cfee444a200298f468908cc9420000000000000000000000000000000000000000000000000000000000000010657468657265756d2d6d61696e6e65740000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000046d616e6100000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000006000000000000000000000000000000000000000000000000000000000000000a00000000000000000000000004d224452801aced8b2f0aebe155379bb5d5943810000000000000000000000000000000000000000000000000000000000000010657468657265756d2d6d61696e6e65740000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000036170650000000000000000000000000000000000000000000000000000000000"  # noqa E501
    start_time = chain.time()
    _, _ = await r.autopay.write(
        "setupDataFeed",
        _reward=2500000000000000,
        _startTime=start_time,
        _queryData=query_data,
        _queryId=query_id,
        _interval=3600,
        _window=300,
        _rewardIncreasePerSecond=1000000000000000,
        _amount=6000000000000000000,
        _priceThreshold=50,
        gas_limit=3500000,
        legacy_gas_price=1,
    )
    chain.mine(timedelta=1)
    reporting_time = chain.time()
    datafeed, tip = await get_feed_and_tip(r.autopay, skip_manual_feeds=False, current_timestamp=reporting_time)
    assert datafeed.query.type == "MimicryMacroMarketMashup"
    time_diff = reporting_time - start_time
    assert tip == 2500000000000000 + (1000000000000000 * time_diff)


@pytest.mark.asyncio
async def test_collection_type(autopay_contract_setup):
    """Test query type MimicryCollectionStat with a query id that doesn't exist in catalog"""
    r = await autopay_contract_setup
    query_id = "0x51f8337e8d8ffeb3538645d22292719d14d48e62ace9b150210db45a9bfef8ad"
    query_data = "0x0000000000000000000000000000000000000000000000000000000000000040000000000000000000000000000000000000000000000000000000000000008000000000000000000000000000000000000000000000000000000000000000154d696d69637279436f6c6c656374696f6e537461740000000000000000000000000000000000000000000000000000000000000000000000000000000000006000000000000000000000000000000000000000000000000000000000000000010000000000000000000000005180db8f5c931aae63c74266b211f580155ecac80000000000000000000000000000000000000000000000000000000000000001"  # noqa: E501
    start_time = chain.time()
    _, _ = await r.autopay.write(
        "setupDataFeed",
        _reward=2500000000000000,
        _startTime=start_time,
        _queryData=query_data,
        _queryId=query_id,
        _interval=3600,
        _window=300,
        _rewardIncreasePerSecond=1000000000000000,
        _amount=6000000000000000000,
        _priceThreshold=50,
        gas_limit=3500000,
        legacy_gas_price=1,
    )
    chain.mine(timedelta=1)
    reporting_time = chain.time()
    datafeed, tip = await get_feed_and_tip(r.autopay, skip_manual_feeds=False, current_timestamp=reporting_time)
    assert datafeed.query.type == "MimicryCollectionStat"
    time_diff = reporting_time - start_time
    assert tip == 2500000000000000 + (1000000000000000 * time_diff)


@pytest.mark.asyncio
async def test_collection_type_build_feed(autopay_contract_setup):
    """Test when feed selection is done through cli and that tip amount
    should be correct when both threshold is triggered or not
    """
    r = await autopay_contract_setup
    typ = "MimicryCollectionStat"
    chain_id = 1
    contract_address = "0x5180db8F5c931aaE63c74266b211F580155ecac8"
    metric = 1
    query_data = HexBytes(
        encode_abi(
            ["string", "bytes"],
            [typ, encode_abi(["uint256", "address", "uint256"], [chain_id, contract_address, metric])],
        )
    )
    query_id = HexBytes(Web3.keccak(query_data))

    start_time = chain.time()
    reward = 2000000000000000
    reward_increase_per_second = 1000000000000000
    _, _ = await r.autopay.write(
        "setupDataFeed",
        _reward=reward,
        _startTime=start_time,
        _queryData=query_data.hex(),
        _queryId=query_id.hex(),
        _interval=3600,
        _window=300,
        _rewardIncreasePerSecond=reward_increase_per_second,
        _amount=6000000000000000000,
        _priceThreshold=50,
        gas_limit=3500000,
        legacy_gas_price=1,
    )
    list_sorted = sorted(DATAFEED_BUILDER_MAPPING)
    choice = list_sorted.index(typ) + 1
    with patch("builtins.input", side_effect=[choice, chain_id, contract_address, metric]):
        feed = build_feed_from_input()
        query_id = feed.query.query_id
        query_data = feed.query.query_data

        chain.mine(timedelta=1)
        reporting_time = chain.time()
        tip_amount = await fetch_feed_tip(autopay=r.autopay, datafeed=feed, timestamp=reporting_time)
        time_diff = reporting_time - start_time
        assert tip_amount == reward + (reward_increase_per_second * time_diff)
        # submit value to remove window eligible submission
        # fake price
        current_price = 1
        await r.oracle.write(
            "submitValue",
            _queryId=query_id,
            _queryData=query_data,
            _value=feed.query.value_type.encode(current_price),
            _nonce=0,
            gas_limit=3500000,
            legacy_gas_price=1,
        )
        chain.mine(timedelta=1)
        new_reporting_time = chain.time()
        # check tip without triggering threshold
        with patch(
            "telliot_feeds.feeds.mimicry_collection_stat_feed.source.fetch_new_datapoint",
            AsyncMock(side_effect=lambda: (current_price, datetime_now_utc())),
        ):
            tip_amount = await fetch_feed_tip(autopay=r.autopay, datafeed=feed, timestamp=new_reporting_time)
            assert tip_amount == 0
        # trigger threshold
        with patch(
            "telliot_feeds.feeds.mimicry_collection_stat_feed.source.fetch_new_datapoint",
            AsyncMock(side_effect=lambda: (current_price + 100, datetime_now_utc())),
        ):
            tip_amount = await fetch_feed_tip(autopay=r.autopay, datafeed=feed, timestamp=new_reporting_time)
            assert tip_amount == reward


@pytest.mark.asyncio
async def test_mashup_type_build_feed(autopay_contract_setup):
    r = await autopay_contract_setup
    list_sorted = sorted(DATAFEED_BUILDER_MAPPING)
    choice = list_sorted.index("MimicryMacroMarketMashup") + 1
    metric = "market-cap"
    currency = "usd"
    collection = (
        ("ethereum-mainnet", "0x50f5474724e0ee42d9a4e711ccfb275809fd6d4a"),
        ("ethereum-mainnet", "0xf87e31492faf9a91b02ee0deaad50d51d56d5d4d"),
        ("ethereum-mainnet", "0x34d85c9cdeb23fa97cb08333b511ac86e1c4e258"),
        ("ethereum-mainnet", "0x790b2cf29ed4f310bf7641f013c65d4560d28371"),
    )
    tokens = (
        ("ethereum-mainnet", "sand", "0x3845badade8e6dff049820680d1f14bd3903a5d0"),
        ("ethereum-mainnet", "mana", "0x0f5d2fb29fb7d3cfee444a200298f468908cc942"),
        ("ethereum-mainnet", "ape", "0x4d224452801aced8b2f0aebe155379bb5d594381"),
    )

    with patch("builtins.input", side_effect=[choice, metric, currency, collection, tokens]):
        feed = build_feed_from_input()
        query_id = feed.query.query_id
        query_data = feed.query.query_data
        start_time = chain.time()
        reward = 1500000000000000
        reward_increase_per_second = 1000000000000000
        _, _ = await r.autopay.write(
            "setupDataFeed",
            _reward=reward,
            _startTime=start_time,
            _queryData=query_data,
            _queryId=query_id,
            _interval=3600,
            _window=300,
            _rewardIncreasePerSecond=reward_increase_per_second,
            _amount=6000000000000000000,
            _priceThreshold=50,
            gas_limit=3500000,
            legacy_gas_price=1,
        )
        chain.mine(timedelta=1)
        reporting_time = chain.time()
        tip_amount = await fetch_feed_tip(autopay=r.autopay, datafeed=feed, timestamp=reporting_time)
        time_diff = reporting_time - start_time
        assert tip_amount == reward + (reward_increase_per_second * time_diff)
