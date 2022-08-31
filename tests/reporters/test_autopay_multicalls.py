"""Test multicall success outcomes requirement True and False"""
import pytest
from multicall import Call
from multicall import Multicall
from telliot_core.apps.core import TelliotCore
from web3.exceptions import ContractLogicError

from telliot_feeds.reporters.reporter_autopay_utils import AutopayCalls


@pytest.fixture
async def setup_autopay_call(mumbai_test_cfg, mock_autopay_contract, multicall_contract) -> AutopayCalls:
    async with TelliotCore(config=mumbai_test_cfg) as core:

        flex = core.get_tellorflex_contracts()
        flex.autopay.address = mock_autopay_contract.address
        flex.autopay.connect()
        calls = AutopayCalls(flex.autopay)
        return calls


@pytest.mark.asyncio
async def test_get_current_tips(setup_autopay_call):
    """Test Multicall by calling getCurrentTip in autopay

    note: getCurrentTip reverts if there are no tips for a given queryid
    """
    calls: AutopayCalls = await setup_autopay_call
    tips = await calls.get_current_tip(require_success=False)
    assert tips["eth-usd-spot"] is None


@pytest.mark.asyncio
async def test_get_current_feeds(setup_autopay_call):
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
        call = [
            Call(
                calls.autopay.address,
                ["fakeFunction(bytes32)(uint256)", b""],
                [["fake_key", None]],
            )
        ]
        multi_call = Multicall(calls=call, _w3=calls.w3, require_success=require_success)
        data = await multi_call.coroutine()
        return data

    calls.get_current_feeds = fake_function

    tips = await calls.get_current_feeds(require_success=False)
    assert tips["fake_key"] is None

    with pytest.raises(ContractLogicError):
        await calls.get_current_feeds(require_success=True)
