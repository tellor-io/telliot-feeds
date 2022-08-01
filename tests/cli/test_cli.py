"""
Unit tests covering telliot-feeds CLI commands.
"""
from io import StringIO
from unittest import mock

import click
import pytest
from click.exceptions import Abort
from click.testing import CliRunner

from telliot_feeds.cli.commands.report import get_stake_amount
from telliot_feeds.cli.commands.report import parse_profit_input
from telliot_feeds.cli.commands.report import valid_diva_chain
from telliot_feeds.cli.main import main as cli_main
from telliot_feeds.cli.utils import build_feed_from_input


def stop():
    click.echo("made it!")
    return


def test_build_feed_from_input(capsys):
    """Test building feed from user input"""

    query_type = "NumericApiResponse"
    url = "https://api.coingecko.com/api/v3/simple/price?ids=uniswap&vs_currencies=usd&include_market_cap=false&include_24hr_vol=false&include_24hr_change=false&include_last_updated_at=falsw"  # noqa: E501
    parse_str = "uniswap, usd"

    with mock.patch("builtins.input", side_effect=[query_type, url, parse_str]):
        feed = build_feed_from_input()
        assert feed.query.type == query_type
        assert feed.query.url == url
        assert feed.query.parseStr == parse_str

        assert feed.source.type == "NumericApiResponseSource"
        assert feed.source.url == url
        assert feed.source.parseStr == parse_str

    query_type = "NumericApiResponse...!!?"
    url = "https://api.coingecko.com/api/v3/simple/price?ids=uniswap&vs_currencies=usd&include_market_cap=false&include_24hr_vol=false&include_24hr_change=false&include_last_updated_at=falsw"  # noqa: E501
    parse_str = "uniswap, usd"

    with mock.patch("builtins.input", side_effect=[query_type, url, parse_str]):
        feed = build_feed_from_input()

        expected = f"No corresponding datafeed found for QueryType: {query_type}"
        captured_output = capsys.readouterr().out.strip()

        assert expected == captured_output


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
    result = runner.invoke(cli_main, ["report", "-qt", "monero-usd-legacy"])

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


def test_get_stake_amount(monkeypatch):
    monkeypatch.setattr("sys.stdin", StringIO("60\n"))
    stake = get_stake_amount()

    assert isinstance(stake, float)
    assert stake == 60.0

    with pytest.raises(Abort):
        monkeypatch.setattr("sys.stdin", StringIO("asdf\n"))
        _ = get_stake_amount()


def test_cmd_settle():
    """Test CLI settle DIVA pool command"""
    runner = CliRunner()
    result = runner.invoke(cli_main, ["--test-config", "settle", "--pool-id", "a;lsdkfj;ak"])

    expected = "Invalid value"

    assert expected in result.output


@pytest.mark.skip("Asking for password when it should not")
def test_query_info():
    """Test getting query info"""
    runner = CliRunner()
    result = runner.invoke(cli_main, ["--test_config", "query", "status", "uspce-legacy"])
    assert not result.exception
    assert "Current value" in result.stdout
