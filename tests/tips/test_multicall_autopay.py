import pytest
from multicall import Call
from telliot_core.apps.core import TelliotCore

from telliot_feeds.reporters.tips.multicall_functions.multicall_autopay import MulticallAutopay


@pytest.fixture(scope="function")
async def setattr_autopay(mumbai_test_cfg):
    async with TelliotCore(config=mumbai_test_cfg) as core:

        flex = core.get_tellor360_contracts()
        call = MulticallAutopay()
        call.autopay = flex.autopay
        return call


@pytest.mark.asyncio
async def test_assemble_call_object(setattr_autopay):
    call: MulticallAutopay = await setattr_autopay

    assemble_call = call.assemble_call_object(
        func_sig="fakefuncsig(uint)(uint)", returns=[[("fake", b"")]], query_id=b""
    )
    assert isinstance(assemble_call, Call)


@pytest.mark.asyncio
async def test_get_data_feed(setattr_autopay):
    call: MulticallAutopay = await setattr_autopay

    assemble_call = call.get_data_feed(feed_id=b"")
    assert isinstance(assemble_call, Call)
    assert assemble_call.function == "getDataFeed(bytes32)((uint256,uint256,uint256,uint256,uint256,uint256,uint256))"
    assert assemble_call.target == call.autopay.address
    assert assemble_call.returns == [[b"", None]]


@pytest.mark.asyncio
async def test_get_multiple_values_before(setattr_autopay):
    call: MulticallAutopay = await setattr_autopay
    assemble_call = call.get_multiple_values_before(query_id=b"", now_timestamp=1234, max_age=1)
    assert isinstance(assemble_call, Call)
    assert assemble_call.function == "getMultipleValuesBefore(bytes32,uint256,uint256,uint256)(bytes[],uint256[])"
    assert assemble_call.target == call.autopay.address
    assert assemble_call.returns == [[("values_array", b""), None], [("timestamps_array", b""), None]]


@pytest.mark.asyncio
async def test_get_reward_claimed_status(setattr_autopay):
    call: MulticallAutopay = await setattr_autopay
    assemble_call = call.get_reward_claimed_status(feed_id=b"", query_id=b"", timestamps=[123, 456])
    assert isinstance(assemble_call, Call)
    assert assemble_call.function == "getRewardClaimStatusList(bytes32,bytes32,uint256[])(bool[])"
    assert assemble_call.target == call.autopay.address
    assert assemble_call.returns == [[(b"", b""), None]]


@pytest.mark.asyncio
async def test_get_current_feeds(setattr_autopay):
    call: MulticallAutopay = await setattr_autopay
    assemble_call = call.get_current_feeds(query_id=b"")
    assert isinstance(assemble_call, Call)
    assert assemble_call.function == "getCurrentFeeds(bytes32)(bytes32[])"
    assert assemble_call.target == call.autopay.address
    assert assemble_call.returns == [[b"", None]]
