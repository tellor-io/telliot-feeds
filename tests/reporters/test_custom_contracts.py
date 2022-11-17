"""
Test using custom contracts for telliot oracle, autopay, or token.

There are two cases where the custom contract CLI flags would be used. First,
if there's an newer deployment of the oracle,
autopay, or token contracts that we want to test. Second, if the user wants to
use a custom reporter contract. In the second case, the user
would still use the --custom-oracle-contract flag. Their custom reporter contract
would need to have an ABI that includes
the same functions as the deployed oracle. Technically, it would only require the
functions that the reporter uses, but
it's easier to just use the same ABI as the deployed oracle. That gas optimization
isn't being made, as it's not a goal to
make the reporter competitive at this time.
"""
import pytest
from telliot_core.apps.core import TelliotCore

from telliot_feeds.utils.reporter_utils import create_custom_contract
from telliot_feeds.utils.reporter_utils import prompt_for_abi


def test_create_custom_contract(
    mumbai_test_cfg,
    mock_token_contract,
    mock_reporter_contract,
    caplog,
):
    """Test creating a custom contract"""
    with TelliotCore(config=mumbai_test_cfg) as core:
        account = core.get_account()

        # Test unable to fetch ABI from block explorer
        with pytest.raises(ValueError):
            _ = create_custom_contract(
                original_contract=mock_token_contract,
                custom_contract_addr="0x0000000000000000000000000000000000000abc",
                endpoint=core.endpoint,
                account=account,
                custom_abi=None,
            )

            assert "Could not retrieve ABI" in caplog.text

        # Test ABI that doesn't match ABI of original contract
        with pytest.raises(ValueError):
            _ = create_custom_contract(
                original_contract=mock_token_contract,
                custom_contract_addr=mock_reporter_contract.address,
                endpoint=core.endpoint,
                account=account,
                custom_abi=["foo"],
            )
            assert "Custom contract ABI must have the same functions as the original contract ABI." in caplog.text


def test_prompt_for_abi():
    """Test prompting for ABI"""
    assert not prompt_for_abi("foo")
