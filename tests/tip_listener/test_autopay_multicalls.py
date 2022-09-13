from ctypes import addressof
import pytest
from brownie import accounts
from telliot_core.apps.core import TelliotCore
from telliot_core.utils.response import ResponseStatus
from telliot_core.utils.timestamp import TimeStamp
from web3 import Web3
from telliot_feeds.queries.query_catalog import query_catalog
from telliot_feeds.reporters.tip_listener.autopay_multicalls import AutopayMulticalls
from multicall import Call
from telliot_feeds.reporters.tip_listener import CATALOG_QUERY_DATA
from telliot_feeds.reporters.tip_listener import CATALOG_QUERY_IDS


query_id = list(CATALOG_QUERY_IDS.keys())[0]
query_data = list(CATALOG_QUERY_DATA.keys())[0]
now_timestamp = TimeStamp.now().ts
month_old_timestamp = now_timestamp - 2_592_000


@pytest.fixture
async def setattr_autopay(autopay_contract_setup):
    call = AutopayMulticalls()
    setattr(call, "autopay", await autopay_contract_setup)
    return call

@pytest.mark.asyncio
async def test_single_autopay_function_call(setattr_autopay):
    call: AutopayMulticalls = await setattr_autopay
    
    assemble_call = call.single_autopay_function_call("fakekey", func_sig="fakefuncsig(uint)(uint)", query_id=b'')
    assert isinstance(assemble_call, Call)

@pytest.mark.asyncio
async def test_get_data_before_calls(setattr_autopay):
    call: AutopayMulticalls = await setattr_autopay

    assemble_get_data_before = call.get_data_before_calls(query_id=b'', now_timestamp=1234)
    assert isinstance(assemble_get_data_before, Call)
    assert assemble_get_data_before.function == "getDataBefore(bytes32,uint256)(bytes,uint256)"
    assert assemble_get_data_before.target == call.autopay.address
    assert assemble_get_data_before.returns == [
        [('current_value', b''), None], [('current_value_timestamp', b''), None]
    ]

@pytest.mark.asyncio
async def test_get_index_for_data_before_now(setattr_autopay):
    call: AutopayMulticalls = await setattr_autopay

    assemble_call = call.get_index_for_data_before_now(query_id=b'', now_timestamp=1234)
    assert isinstance(assemble_call, Call)
    assert assemble_call.function == "getIndexForDataBefore(bytes32,uint256)(bool,uint256)"
    assert assemble_call.target == call.autopay.address
    assert assemble_call.returns == [
        [('current_status', b''), None], [('current_value_index', b''), None]
    ]

@pytest.mark.asyncio
async def test_get_index_for_data_before_month(setattr_autopay):
    call: AutopayMulticalls = await setattr_autopay

    assemble_call = call.get_index_for_data_before_month(query_id=b'', month_old=1234)
    assert isinstance(assemble_call, Call)
    assert assemble_call.function == "getIndexForDataBefore(bytes32,uint256)(bool,uint256)"
    assert assemble_call.target == call.autopay.address
    assert assemble_call.returns == [
        [('month_old_status', b''), None], [('month_old_index', b''), None]
    ]

@pytest.mark.asyncio
async def test_get_timestamp_by_query_id_and_index(setattr_autopay):
    call: AutopayMulticalls = await setattr_autopay
    index = 0
    assemble_call = call.get_timestamp_by_query_id_and_index(query_id=b'', index=index)
    assert isinstance(assemble_call, Call)
    assert assemble_call.function == "getTimestampbyQueryIdandIndex(bytes32,uint256)(uint256)"
    assert assemble_call.target == call.autopay.address
    assert assemble_call.returns == [
        [(index, b''), None]
    ]

@pytest.mark.asyncio
async def test_get_reward_claimed_status(setattr_autopay):
    call: AutopayMulticalls = await setattr_autopay
    assemble_call = call.get_reward_claimed_status(feed_id=b'', query_id=b'', timestamps=[123,456])
    assert isinstance(assemble_call, Call)
    assert assemble_call.function == "getRewardClaimStatusList(bytes32,bytes32,uint256[])(bool[])"
    assert assemble_call.target == call.autopay.address