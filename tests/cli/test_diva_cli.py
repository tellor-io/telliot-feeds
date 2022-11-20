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


def test_available_cmds():
    """Test help command for integrations."""
    runner = CliRunner()
    result = runner.invoke(cli_main, ["integrations", "--help"])

    assert result.exit_code == 0
    assert "diva  Commands for Diva Protocol integration." in result.stdout

    result = runner.invoke(cli_main, ["integrations", "diva", "--help"])

    assert result.exit_code == 0
    assert "Commands for interacting with reported/settled pools cache" in result.stdout

    result = runner.invoke(cli_main, ["integrations", "diva", "cache", "--help"])
    view_msg = "view   View reported/settled pools cache."
    clear_msg = "clear  Clear reported/settled pools cache."

    assert result.exit_code == 0
    assert view_msg in result.stdout
    assert clear_msg in result.stdout


def test_diva_help_cmd():
    # ensure diva options (report / settle) are available
    pass


def test_report_cmd():
    # telliot-feeds integrations diva report
    pass


def test_settle_cmd():
    # telliot-feeds integrations diva settle --pool-id=<id>
    pass
