"""Test multicall success outcomes requirement True and False"""
from unittest.mock import patch

import pytest
from multicall import Call
from multicall import Multicall
from telliot_core.apps.core import TelliotCore
from web3.exceptions import ContractLogicError

from telliot_feeds.reporters import reporter_autopay_utils
from telliot_feeds.reporters.reporter_autopay_utils import autopay_suggested_report
from telliot_feeds.reporters.reporter_autopay_utils import AutopayCalls
from telliot_feeds.reporters.reporter_autopay_utils import safe_multicall


def fake_call(calls: AutopayCalls):
    """helper function returning consistent fake multicall"""
    return [
        Call(
            calls.autopay.address,
            ["fakeFunction(bytes32)(uint256)", b""],
            [["fake_key", None]],
        )
    ]


@pytest.fixture(scope="function")
async def setup_autopay_call(mumbai_test_cfg, mock_autopay_contract) -> AutopayCalls:
    async with TelliotCore(config=mumbai_test_cfg) as core:

        flex = core.get_tellorflex_contracts()
        flex.autopay.address = mock_autopay_contract.address
        flex.autopay.connect()
        calls = AutopayCalls(flex.autopay)
        return calls


@pytest.mark.asyncio
async def test_get_current_tips(setup_autopay_call):
    """Test Multicall by calling getCurrentTip in autopay"""
    calls: AutopayCalls = await setup_autopay_call
    tips = await calls.get_current_tip(require_success=False)
    assert tips["eth-usd-spot"] == 0


@pytest.mark.asyncio
async def test_get_current_feeds(caplog, setup_autopay_call):
    """Test getCurrentFeeds call in autopay using multicall"""
    calls: AutopayCalls = await setup_autopay_call
    # test proper function for success outcomes
    boolean = [True, False]
    for i in boolean:
        tips = await calls.get_current_feeds(require_success=i)
        assert tips["eth-usd-spot"] == ()
        assert tips[("eth-usd-spot", "current_time")] == 0
        assert tips[("eth-usd-spot", "three_mos_ago")] == 0

    async def fake_function(require_success=True):
        """fake function signature call that doesn't exist in autopay
        should revert as a ContractLogicError"""

        return await safe_multicall(calls=fake_call(calls), endpoint=calls.w3, require_success=require_success)

    calls.get_current_feeds = fake_function

    tips = await calls.get_current_feeds(require_success=False)
    assert tips["fake_key"] is None

    true_result = await calls.get_current_feeds(require_success=True)
    assert true_result is None
    assert "Contract reversion in multicall request" in caplog.text


@pytest.mark.asyncio
async def test_safe_multicall(caplog, setup_autopay_call):
    """Test safe multicall with error handling"""
    calls: AutopayCalls = await setup_autopay_call

    def raise_unsupported_block_num():
        raise ValueError({"code": -32000, "message": "unsupported block number 22071635"})

    def raise_unexpected_rpc_error():
        raise ValueError({"code": -32000, "message": "unexpected rpc error nooooo"})

    def raise_contract_reversion():
        raise ContractLogicError

    with patch.object(Multicall, "coroutine", side_effect=raise_unsupported_block_num):

        res = await safe_multicall(fake_call(calls), endpoint=calls.w3, require_success=True)

        assert res is None
        assert "ValueError" in caplog.text

    with patch.object(Multicall, "coroutine", side_effect=raise_unexpected_rpc_error):

        res = await safe_multicall(fake_call(calls), endpoint=calls.w3, require_success=True)

        assert res is None
        assert "ValueError" in caplog.text

    with patch.object(Multicall, "coroutine", side_effect=raise_contract_reversion):

        res = await safe_multicall(fake_call(calls), endpoint=calls.w3, require_success=True)

        assert res is None
        assert "Contract reversion in multicall request" in caplog.text


@pytest.mark.asyncio
async def test_index_error(setup_autopay_call, caplog):
    bad_response = {
        "ric-usd-spot": (),
        "disregard_boolean": None,
        ("ric-usd-spot", "current_time"): None,
        ("ric-usd-spot", "three_mos_ago"): None,
    }
    call: AutopayCalls = await setup_autopay_call

    async def fake_func():
        return bad_response

    call.get_current_feeds = fake_func
    res = await call.reward_claim_status()
    assert res == (None, None, None)
    assert "No feeds balance to check"


@pytest.mark.asyncio
async def test_multicall_return_none(setup_autopay_call):
    calls: AutopayCalls = await setup_autopay_call

    async def none(x, y, z):
        return None

    reporter_autopay_utils.safe_multicall = none
    resp = await calls.get_current_feeds()
    assert resp is None
    resp = await autopay_suggested_report(calls.autopay)
    assert resp == (None, None)
