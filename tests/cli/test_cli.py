"""
Unit tests covering telliot_core CLI commands.
"""
import os

import pytest
from click.testing import CliRunner

from telliot_feed_examples.cli import cli
from telliot_feed_examples.cli import get_app
from telliot_feed_examples.cli import parse_profit_input
from telliot_feed_examples.feeds import LEGACY_DATAFEEDS


def test_parse_profit_input():
    """Test reading in custom expected profit from user."""
    result = parse_profit_input("YOLO")
    assert isinstance(result, str)
    assert result == "YOLO"

    result = parse_profit_input("1234.1234")
    assert isinstance(result, float)
    assert result == 1234.1234

    result = parse_profit_input("asdf")
    assert result is None


@pytest.mark.skip
def test_get_app():
    """Test instantiating TelliotCore app using click Context."""
    ctx = {
        "CHAIN_ID": 4,  # Rinkeby testnet
        "RPC_URL": os.getenv("NODE_URL", None),
        "PRIVATE_KEY": os.getenv("PRIVATE_KEY", None),
    }
    core = get_app(ctx)

    assert core.config
    assert core.tellorx


@pytest.mark.skip
def test_cmd_report():
    """Test report command."""
    runner = CliRunner()
    result = runner.invoke(cli, ["report", "--legacy-id", "1234"])

    assert result.exit_code == 0

    expected = f"Invalid legacy ID. Valid choices: {', '.join(list(LEGACY_DATAFEEDS))}"
    assert expected in result.output


def test_custom_gas_flag():
    """Test using a custom gas."""
    # Test incorrect command invocation
    runner = CliRunner()
    result = runner.invoke(cli, ["report", "--ges-limit", "250000"])

    assert result.exit_code == 2

    expected = "Error: No such option: --ges-limit Did you mean --gas-limit?"
    assert expected in result.output

    # Test incorrect type
    result = runner.invoke(cli, ["report", "-gl", "blah"])

    assert result.exit_code == 2

    expected = (
        "Error: Invalid value for '--gas-limit' / '-gl': 'blah' is not a valid integer."
    )
    assert expected in result.output


def test_cmd_tip():
    """Test CLI tip command"""
    runner = CliRunner()
    trb = "0.00001"
    result = runner.invoke(cli, ["tip", "--amount-usd", trb])

    expected = "Error: No such option: --amount-usd Did you mean --amount-trb?"

    assert expected in result.output


# TODO: test successful CLI runs and all option flags
