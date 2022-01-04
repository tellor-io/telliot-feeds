"""
Unit tests covering telliot_core CLI commands.
"""
import pytest
from click.testing import CliRunner

from telliot_feed_examples.cli import cli
from telliot_feed_examples.cli import parse_profit_input


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


# TODO: test passes, but getting this error:
# asyncio:base_events.py:1738 Unclosed client session
# which breaks later tests because TelliotCore singleton
# already exists
@pytest.mark.skip
def test_flag_staker_tag():
    """Test user choosing to use different staker."""
    runner = CliRunner()
    result = runner.invoke(cli, ["-st", "thisdoesnotexist", "report"])

    assert result.exception
    assert result.exit_code == 1

    expected = "No staker found for given tag, using default"
    assert expected in result.stdout


def test_cmd_report():
    """Test report command."""
    runner = CliRunner()
    result = runner.invoke(cli, ["-nfb", "report", "-lid", "1234"])

    assert result.exception
    assert result.exit_code == 2

    expected = "Invalid value for '--legacy-id'"
    assert expected in result.stdout


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
    result = runner.invoke(cli, ["--test_config", "tip", "--amount-usd", trb])

    expected = "Error: No such option: --amount-usd Did you mean --amount-trb?"

    assert expected in result.output
