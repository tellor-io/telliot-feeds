import sys
from unittest import mock

from click.testing import CliRunner

from telliot_feeds.cli.main import main as cli_main


def test_invalid_diva_diamond_address():
    """Test checking for invalid diva diamond address."""
    runner = CliRunner()
    result = runner.invoke(cli_main, ["report", "-dpt", "true", "-dda", "1234"])

    assert result.exception
    assert result.exit_code == 2

    assert "Address must be a valid hex string" in result.stdout


def test_invalid_diva_middleware_address():
    """Test checking for invalid diva middleware address."""
    runner = CliRunner()
    result = runner.invoke(cli_main, ["report", "-dpt", "true", "-dma", "1234"])

    assert result.exception
    assert result.exit_code == 2

    assert "Address must be a valid hex string" in result.stdout


def test_default_values_available():
    """Make sure default contract addresses are available."""
    runner = CliRunner()

    # mock expected_profit() call so cli quits early
    def mock_parse_profit(*args, **kwargs):
        sys.exit(0)

    with mock.patch("telliot_feeds.cli.commands.report.parse_profit_input", side_effect=mock_parse_profit):
        result = runner.invoke(cli_main, ["report", "--build-feed", "-p", "YOLO"])

        assert result.exit_code == 0


def test_integrations_help_cmd():
    # ensure diva cmd is available
    pass


def test_diva_help_cmd():
    # ensure diva options (report / settle) are available
    pass


def test_report_cmd():
    # telliot-feeds integrations diva report
    pass


def test_settle_cmd():
    # telliot-feeds integrations diva settle --pool-id=<id>
    pass
