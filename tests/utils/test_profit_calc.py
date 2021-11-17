"""
Test covering Pytelliot EVM contract connection utils.
"""
import pytest

from telliot_feed_examples.utils.profitcalc import profitable


@pytest.fixture
@pytest.mark.asyncio
async def rewards(oracle):
    """For rewards calculation"""
    query_id = "0x0000000000000000000000000000000000000000000000000000000000000002"

    time_based_reward, _ = await oracle.read(func_name="getTimeBasedReward")
    current_tip, _ = await oracle.read(func_name="getCurrentReward", _queryId=query_id)

    return time_based_reward, current_tip[0]


# @pytest.mark.skip("uninvestigated error")
def test_is_not_profitable(rewards):
    """Test profitability with time based reward and current tip of 0"""
    time_based_reward, current_tip = rewards

    assert time_based_reward == 5e17
    assert current_tip == 0
    assert not profitable(
        tb_reward=time_based_reward, tip=current_tip, gas=1, gas_price=1e1000
    )


# @pytest.mark.skip("uninvestigated error")
def test_is_profitable(rewards):
    """Test profitability with a tip"""
    time_based_reward, _ = rewards

    assert time_based_reward == 5e17
    assert profitable(tb_reward=time_based_reward, tip=1, gas=1, gas_price=1)
