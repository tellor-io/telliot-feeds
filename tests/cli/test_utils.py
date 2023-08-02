from unittest import mock

import pytest
from hexbytes import HexBytes

from telliot_feeds.cli.utils import build_query
from telliot_feeds.cli.utils import call_oracle
from telliot_feeds.cli.utils import CustomHexBytes
from telliot_feeds.queries.abi_query import AbiQuery
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.reporters.stake import Stake


def test_build_query():
    """Test building a query."""
    queries = [q for q in AbiQuery.__subclasses__() if q.__name__ not in ("LegacyRequest")]
    options = sorted([q.__name__ for q in queries])
    idx = options.index("SpotPrice")
    with (
        mock.patch("simple_term_menu.TerminalMenu.show", return_value=idx),
        mock.patch("click.prompt", side_effect=["eth", "usd"]),
    ):
        query = build_query()
        assert isinstance(query, SpotPrice)
        assert query.asset == "eth"
        assert query.currency == "usd"


@pytest.mark.asyncio
async def test_call_oracle(tellor_360, caplog, chain):
    """Test calling the oracle."""
    user_inputs = {
        "min_native_token_balance": 0.0,
        "gas_limit": 350000,
        "base_fee_per_gas": None,
        "priority_fee_per_gas": None,
        "max_fee_per_gas": None,
        "legacy_gas_price": 100,
        "transaction_type": 0,
        "gas_multiplier": None,
    }

    contracts, account = tellor_360
    s = Stake(
        oracle=contracts.oracle,
        token=contracts.token,
        endpoint=contracts.oracle.node,
        account=account,
        **user_inputs,
    )

    _ = await s.deposit_stake(int(1 * 1e18))

    class ctx:
        def __init__(self):
            self.obj = {"CHAIN_ID": 80001, "ACCOUNT_NAME": "brownie-acct", "TEST_CONFIG": None}

    user_inputs["password"] = ""
    with mock.patch("telliot_core.apps.core.TelliotCore.get_tellor360_contracts", return_value=contracts):
        with mock.patch("click.confirm", return_value="y"):
            await call_oracle(
                ctx=ctx(),
                func="requestStakingWithdraw",
                user_inputs=user_inputs,
                _amount=1,
            )
            assert "requestStakingWithdraw transaction succeeded" in caplog.text
            user_inputs["password"] = ""
            user_inputs["min_native_token_balance"] = 0.0
            await call_oracle(
                ctx=ctx(),
                func="withdrawStake",
                user_inputs=user_inputs,
            )
            assert "revert 7 days didn't pass" in caplog.text
            chain.sleep(604800)
            user_inputs["password"] = ""
            user_inputs["min_native_token_balance"] = 0.0
            await call_oracle(
                ctx=ctx(),
                func="withdrawStake",
                user_inputs=user_inputs,
            )
            assert "withdrawStake transaction succeeded" in caplog.text


def test_custom_hexbytes_wrapper():
    """Test custom hexbytes wrapper."""
    # test when 0x is present and not present
    for value in (CustomHexBytes("0x1234"), CustomHexBytes("1234")):
        value = CustomHexBytes("0x1234")
        assert value.hex() == "0x1234"
        assert isinstance(value, CustomHexBytes)
        assert isinstance(value, HexBytes)
        assert isinstance(value, bytes)
    with pytest.raises(ValueError):
        CustomHexBytes(1)
        CustomHexBytes(1.1)
        CustomHexBytes(True)
        CustomHexBytes(False)
