"""
Unit tests covering telliot_core CLI commands.
"""
from click.testing import CliRunner

from telliot_feed_examples.cli import cli
from telliot_feed_examples.feeds import LEGACY_DATAFEEDS


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


def test_rpc_override():
    """Test the CLI option to override the RPC url provided in configs"""
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "--rpc-ur",
            "wss://rinkeby.infura.io/ws/v3/1a09c4705f114af2997548dd901d655b",
            "report",
            "--submit-once",
        ],
    )

    expected = "Error: No such option: --rpc-ur (Possible options: --rpc-url, -rpc)"

    assert expected in result.output

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "--rpc-url",
            "wss://goerli.infura.io/ws/v3/1a09c4705f114af2997548dd901d655b",
            "report",
            "--submit-once",
        ],
    )

    assert "Current chain ID: 5" in result.output


# TODO: test successful CLI runs and all option flags
