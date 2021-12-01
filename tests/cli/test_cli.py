"""
Unit tests covering telliot_core CLI commands.
"""
from click.testing import CliRunner

from telliot_feed_examples.cli import cli
from telliot_feed_examples.feeds import LEGACY_DATAFEEDS


def test_cmd_report():
    """Test report command."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--legacy-id", "1234", "report"])

    assert result.exit_code == 1

    expected = f"Invalid legacy ID. Valid choices: {', '.join(list(LEGACY_DATAFEEDS))}"
    assert expected in result.output

    # TODO: test successful reporting and all other option flags


def test_cmd_tip():
    """Test CLI tip command"""
    runner = CliRunner()
    trb = "0.00001"
    result = runner.invoke(cli, ["-lid", "1", "tip", "--amount-trb", trb])

    expected1 = "Tipping 1e-05 TRB for legacy ID 1."
    expected2 = "Success!"

    assert expected1 in result.output
    assert expected2 in result.output
