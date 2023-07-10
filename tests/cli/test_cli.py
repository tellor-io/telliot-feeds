"""
Unit tests covering telliot-feeds CLI commands.
"""
from unittest import mock

import click
import pytest
from click.testing import CliRunner

from telliot_feeds.cli.commands.report import valid_diva_chain
from telliot_feeds.cli.constants import STAKE_MESSAGE
from telliot_feeds.cli.main import main as cli_main
from telliot_feeds.cli.utils import build_feed_from_input
from telliot_feeds.cli.utils import parse_profit_input


def stop():
    click.echo("made it!")
    return


def test_build_feed_from_input(capsys):
    """Test building feed from user input"""

    num_choice = 12  # NumericApiResponse is the 11th option
    url = "https://api.coingecko.com/api/v3/simple/price?ids=uniswap&vs_currencies=usd&include_market_cap=false&include_24hr_vol=false&include_24hr_change=false&include_last_updated_at=falsw"  # noqa: E501
    parse_str = "uniswap, usd"

    with mock.patch("builtins.input", side_effect=[num_choice, url, parse_str]):
        feed = build_feed_from_input()
        assert feed.query.type == "NumericApiResponse"
        assert feed.query.url == url
        assert feed.query.parseStr == parse_str

        assert feed.source.type == "NumericApiResponseSource"
        assert feed.source.url == url
        assert feed.source.parseStr == parse_str

    num_choice = 420
    url = "https://api.coingecko.com/api/v3/simple/price?ids=uniswap&vs_currencies=usd&include_market_cap=false&include_24hr_vol=false&include_24hr_change=false&include_last_updated_at=falsw"  # noqa: E501
    parse_str = "uniswap, usd"

    with mock.patch("builtins.input", side_effect=[num_choice, url, parse_str]):
        with pytest.raises(StopIteration):
            _ = build_feed_from_input()

            assert "Invalid choice" in capsys.readouterr().out.strip()


def test_build_evm_call_feed_from_input(capsys):
    """Test building a feed from user input for EVMCall query type"""
    num_choice = 6  # EVMCall is the 5th option
    chain_id_str = "1"
    chain_id = 1
    contract_address = "0x88dF592F8eb5D7Bd38bFeF7dEb0fBc02cf3778a0"
    calldata = b"\x18\x16\x0d\xdd"
    calldata_as_str = "0x18160ddd"

    with mock.patch("builtins.input", side_effect=[num_choice, chain_id_str, contract_address, calldata_as_str]):
        feed = build_feed_from_input()
        assert feed.query.type == "EVMCall"
        assert feed.query.chainId == chain_id
        assert feed.query.contractAddress == contract_address
        assert feed.query.calldata == calldata

        assert feed.source.type == "EVMCallSource"
        assert feed.source.chainId == chain_id
        assert feed.source.contractAddress == contract_address
        assert feed.source.calldata == calldata


def test_parse_profit_input():
    """Test reading in custom expected profit from user."""
    result = parse_profit_input({}, None, "YOLO")
    assert isinstance(result, str)
    assert result == "YOLO"

    result = parse_profit_input({}, None, "1234.1234")
    assert isinstance(result, float)
    assert result == 1234.1234

    with pytest.raises(click.BadParameter):
        _ = parse_profit_input({}, None, "asdf")


@pytest.mark.skip
def test_flag_staker_tag():
    """Test user choosing to use different staker."""
    runner = CliRunner()
    result = runner.invoke(cli_main, ["-st", "thisdoesnotexist", "report"])

    assert result.exception
    assert result.exit_code == 1

    expected = "No staker found for given tag, using default"
    assert expected in result.stdout


def test_invalid_report_option_query_tag():
    """Test selecting datafeed using wrong query tag."""
    runner = CliRunner()
    result = runner.invoke(cli_main, ["report", "-qt", "monero-usd-blah"])

    assert result.exception
    assert result.exit_code == 2

    expected = "Invalid value for '--query-tag' / '-qt'"
    assert expected in result.stdout


def test_custom_gas_flag():
    """Test using a custom gas."""
    # Test incorrect command invocation
    runner = CliRunner()
    result = runner.invoke(cli_main, ["report", "--ges-limit", "250000"])

    assert result.exit_code == 2

    expected = "Error: No such option: --ges-limit Did you mean --gas-limit?"
    assert expected in result.output

    # Test incorrect type
    result = runner.invoke(cli_main, ["report", "-gl", "blah"])

    assert result.exit_code == 2

    expected = "Error: Invalid value for '--gas-limit' / '-gl': 'blah' is not a valid integer."
    assert expected in result.output


def test_diva_protocol_invalid_chain():
    valid = valid_diva_chain(chain_id=1)

    assert not valid


@pytest.mark.skip("Disabled until we need this functionality")
def test_cmd_tip():
    """Test CLI tip command"""
    runner = CliRunner()
    trb = "0.00001"
    result = runner.invoke(cli_main, ["--test_config", "tip", "--amount-usd", trb])

    expected = "Error: No such option: --amount-usd Did you mean --amount-trb?"

    assert expected in result.output


def test_stake_flag():
    """Test using the stake flag."""
    runner = CliRunner()
    result = runner.invoke(cli_main, ["report", "--stake", "asdf"])

    assert result.exception
    assert result.exit_code == 2

    expected = "Error: Invalid value for '--stake' / '-s': 'asdf' is not a valid float."
    assert expected in result.stdout

    # check stake option description in help message
    result = runner.invoke(cli_main, ["report", "--help"])

    print("HERE", result.stdout)
    assert result.exit_code == 0
    assert "".join([s.strip() for s in STAKE_MESSAGE.split()]) in "".join([s.strip() for s in result.stdout.split()])


def test_report_options_available():
    """Ensure check_rewards & use_random_feeds options available."""
    runner = CliRunner()
    result = runner.invoke(cli_main, ["report", "--help"])

    assert result.exit_code == 0
    assert "--check-rewards" in result.stdout
    assert "--random-feeds" in result.stdout


def test_cmd_settle():
    """Test CLI settle DIVA pool command"""
    runner = CliRunner()
    result = runner.invoke(cli_main, ["--test-config", "settle", "--pool-id", 1])

    expected = "Invalid value"

    assert expected in result.output


@pytest.mark.skip("Asking for password when it should not")
def test_query_info():
    """Test getting query info"""
    runner = CliRunner()
    result = runner.invoke(cli_main, ["--test_config", "query", "status", "-qt", "eth-usd-spot"])
    assert not result.exception
    assert "Current value" in result.stdout


def test_config_show():
    """Make sure config is running"""
    runner = CliRunner()
    result = runner.invoke(cli_main, ["--test-config", "config", "show"])
    assert not result.exception


def test_config_cmd():
    """Test telliot_core CLI command: report."""
    runner = CliRunner()
    result = runner.invoke(cli_main, ["config", "init"])
    assert not result.exception
    print(result.stdout)


def test_account_cmd():
    """Test command: account."""
    runner = CliRunner()
    result = runner.invoke(cli_main, ["account", "--help"])
    msg = result.stdout.lower()

    assert not result.exception
    assert "find" in msg
    assert "create" in msg
    assert "key" in msg
    assert "delete" in msg


def test_no_accounts_msg():
    """Test no accounts message appears."""

    def mock_find_accounts(*args, **kwargs):
        click.echo("mocking find_accounts")
        return []

    with mock.patch("telliot_feeds.cli.commands.report.find_accounts", side_effect=mock_find_accounts):
        runner = CliRunner()
        result = runner.invoke(cli_main, ["report", "-a", "noaccountassociatedwiththisname"])
        msg = result.stdout.lower()

        assert not result.exception
        assert "no account found" in msg
