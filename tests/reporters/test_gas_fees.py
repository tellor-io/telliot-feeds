from unittest.mock import Mock
from unittest.mock import PropertyMock

import pytest
from telliot_core.apps.core import TelliotCore
from web3.datastructures import AttributeDict

from telliot_feeds.reporters.gas import GasFees


@pytest.fixture(scope="function")
async def gas_fees_object(mumbai_test_cfg):
    """Fixture that build GasFees object."""
    async with TelliotCore(config=mumbai_test_cfg) as core:
        # get PubKey and PrivKey from config files
        account = core.get_account()

        gas = GasFees(
            endpoint=core.endpoint,
            account=account,
            transaction_type=0,
            legacy_gas_price=None,
            gas_multiplier=1,
            priority_fee_per_gas=None,
            base_fee_per_gas=None,
            max_fee_per_gas=None,
            gas_limit=None,
        )
        return gas


@pytest.mark.asyncio
async def test_get_legacy_gas_price(gas_fees_object):
    gas: GasFees = await gas_fees_object

    legacy_gas_price, status = gas.get_legacy_gas_price()
    assert status.ok
    assert "gasPrice" in legacy_gas_price
    assert legacy_gas_price["gasPrice"] is not None, "get_legacy_gas_price returned None"
    assert legacy_gas_price["gasPrice"] > 0, "legacy gas price not fetched properly"
    gas.web3 = Mock()
    type(gas.web3.eth).gas_price = PropertyMock(return_value=None)
    legacy_gas_price, status = gas.get_legacy_gas_price()
    assert not status.ok
    assert legacy_gas_price is None
    assert status.error == "Error fetching legacy gas price, rpc returned None"

    type(gas.web3.eth).gas_price = PropertyMock(side_effect=ValueError("Mock Error"))
    legacy_gas_price, status = gas.get_legacy_gas_price()
    assert not status.ok
    assert legacy_gas_price is None
    assert status.error == "Error fetching legacy gas price: ValueError('Mock Error')"


@pytest.mark.asyncio
async def test_get_eip1559_gas_price(gas_fees_object):
    gas: GasFees = await gas_fees_object
    mock_fee_history = AttributeDict(
        {
            "baseFeePerGas": [13676801331, 14273862890, 13972887310, 14813623596, 14046654284, 13615655875],
            "reward": [
                [100000000, 100000000, 1500000000],
                [100000000, 100000000, 1500000000],
                [100000000, 1000000000, 3000000000],
                [100000000, 528000000, 2000000000],
                [100000000, 103445451, 1650000000],
            ],
        }
    )

    type(gas.web3.eth).fee_history = Mock(return_value=mock_fee_history)
    eip1559_gas_price, status = gas.get_eip1559_gas_price()
    assert status.ok
    assert eip1559_gas_price["maxPriorityFeePerGas"] == 1000000000
    base_fee = mock_fee_history["baseFeePerGas"][-1]
    assert eip1559_gas_price["maxFeePerGas"] == gas.get_max_fee(base_fee)
    # fee history is None
    type(gas.web3.eth).fee_history = Mock(return_value=None)
    eip1559_gas_price, status = gas.get_eip1559_gas_price()
    assert not status.ok
    assert eip1559_gas_price is None
    assert "no base fee set" in status.error
    # exception when fetching fee history
    type(gas.web3.eth).fee_history = Mock(side_effect=ValueError("Mock Error"))
    eip1559_gas_price, status = gas.get_eip1559_gas_price()
    assert not status.ok
    assert eip1559_gas_price is None
    assert "Error fetching fee history" in status.error
    assert "unable to fetch history to set base fee" in status.error
    # when 2 out 3 fee args are user provided fee history from node isn't used
    # instead maxFeePerGas is calculated from user provided values
    type(gas.web3.eth).fee_history = Mock(return_value=mock_fee_history)
    gas.priority_fee_per_gas = 1  # 1 Gwei. users provide gwei value
    gas.base_fee_per_gas = 136
    eip1559_gas_price, status = gas.get_eip1559_gas_price()
    assert status.ok
    assert eip1559_gas_price["maxPriorityFeePerGas"] == 1
    assert eip1559_gas_price["maxFeePerGas"] == gas.get_max_fee(136)

    # when 1 out 3 fee args are user provided fee history from node used
    # and maxFeePerGas and priority fee are calculated from fee history
    type(gas.web3.eth).fee_history = Mock(return_value=mock_fee_history)
    gas.priority_fee_per_gas = None
    gas.base_fee_per_gas = gas.from_gwei(150)
    eip1559_gas_price, status = gas.get_eip1559_gas_price()
    assert status.ok
    assert eip1559_gas_price["maxPriorityFeePerGas"] == 1000000000  # 1 Gwei
    assert eip1559_gas_price["maxFeePerGas"] == gas.get_max_fee(gas.from_gwei(150))


@pytest.mark.asyncio
async def test_update_gas_fees(gas_fees_object):
    gas: GasFees = await gas_fees_object
    status = gas.update_gas_fees()
    assert status.ok, "update_gas_fees returned not ok status"
    assert gas.gas_info["gasPrice"] is not None, "gas_info['gasPrice'] returned None"
    assert gas.gas_info["gasPrice"] > 0, "gas_info['gasPrice'] is not fetched properly"
    assert gas.gas_info["gas"] is None
    assert gas.gas_info["maxFeePerGas"] is None
    assert gas.gas_info["maxPriorityFeePerGas"] is None
    gas_info_core = {
        "gas_limit": None,
        "max_fee_per_gas": None,
        "max_priority_fee_per_gas": None,
        "legacy_gas_price": 20.2,
    }
    assert gas.get_gas_info_core() == gas_info_core

    gas.web3 = Mock()
    type(gas.web3.eth).gas_price = PropertyMock(return_value=None)
    status = gas.update_gas_fees()
    assert not status.ok
    assert "Failed to update gas fees for legacy type transaction:" in status.error
    assert gas.gas_info["gasPrice"] is None, "gas_info['gasPrice'] should be None since gas update failed"
    # set gas price to None and check if gas info is updated properly
    gas_info_core["legacy_gas_price"] = None
    assert gas.get_gas_info_core() == gas_info_core

    # change to type 2 transactions
    mock_fee_history = AttributeDict(
        {
            "baseFeePerGas": [13676801331, 14273862890, 13972887310, 14813623596, 14046654284, 13615655875],
            "reward": [
                [100000000, 100000000, 1500000000],
                [100000000, 100000000, 1500000000],
                [100000000, 1000000000, 3000000000],
                [100000000, 528000000, 2000000000],
                [100000000, 103445451, 1650000000],
            ],
        }
    )
    gas.transaction_type = 2
    type(gas.web3.eth).fee_history = Mock(return_value=mock_fee_history)
    type(gas.web3.eth)._max_priority_fee = Mock(return_value=gas.from_gwei(1))
    status = gas.update_gas_fees()
    base_fee = mock_fee_history["baseFeePerGas"][-1]
    assert status.ok
    assert gas.gas_info["gasPrice"] is None
    assert gas.gas_info["gas"] is None
    assert gas.gas_info["maxFeePerGas"] is not None
    assert gas.gas_info["maxFeePerGas"] == gas.get_max_fee(base_fee)
    assert gas.gas_info["maxPriorityFeePerGas"] == 1000000000

    type(gas.web3.eth).fee_history = Mock(side_effect=ValueError("Mock Error"))
    status = gas.update_gas_fees()
    assert gas.gas_info["maxFeePerGas"] is None
    assert gas.gas_info["maxPriorityFeePerGas"] is None
    assert "Failed to update gas fees for EIP1559 type transaction:" in status.error

    gas.transaction_type = 5
    status = gas.update_gas_fees()
    assert gas.gas_info["maxFeePerGas"] is None
    assert gas.gas_info["maxPriorityFeePerGas"] is None
    assert "Failed to update gas fees: invalid transaction type: 5" in status.error
