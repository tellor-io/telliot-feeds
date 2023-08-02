from click.testing import CliRunner

from telliot_feeds.cli.main import main as cli_main


def test_request_withdraw_cmd():
    """Test request withdraw stake command."""
    runner = CliRunner()
    result = runner.invoke(cli_main, ["request-withdraw", "-a", "git-tellorflex-test-key"])
    assert "Missing option '--amount' / '-amt'" in result.stdout
    assert result.exception
    assert result.exit_code == 2


def test_withdraw_cmd():
    """Test withdraw stake command."""
    runner = CliRunner()
    result = runner.invoke(cli_main, ["withdraw"])
    assert result.exception
    assert result.exit_code == 2


def test_staking_cmd():
    """Test stake command."""
    runner = CliRunner()
    result = runner.invoke(cli_main, ["stake", "-a", "git-tellorflex-test-key"])
    assert "Missing option '--amount' / '-amt'" in result.stdout
    assert result.exception
    assert result.exit_code == 2
