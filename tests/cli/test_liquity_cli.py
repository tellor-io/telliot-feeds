from click.testing import CliRunner

from telliot_feeds.cli.main import main as cli_main


def test_no_chainlink_feed_found():
    """Test no address found."""
    runner = CliRunner()
    result = runner.invoke(cli_main, ["liquity", "-a", "git-tellorflex-test-key"])
    assert result.exception
    assert result.exit_code == 2

    expected = "Chain link feed not found for chain id: 1337"
    assert expected in result.stdout

    runner = CliRunner()
    result = runner.invoke(cli_main, ["liquity", "-a", "git-tellorflex-test-key", "-clf", "0x"])
    print(result.stdout, result.exception)
    assert result.exception
    assert result.exit_code == 2

    expected = "Error: Invalid chain link feed address"
    assert expected in result.stdout


def test_invalid_inputs():
    """Test non numeric inputs."""
    runner = CliRunner()
    result = runner.invoke(cli_main, ["liquity", "-a", "git-tellorflex-test-key", "-pc", "asdf"])

    assert result.exception
    assert result.exit_code == 2

    expected = "Error: Invalid value for '-pc' / '--percent-change': 'asdf' is not a valid float."
    assert expected in result.stdout

    runner = CliRunner()
    result = runner.invoke(cli_main, ["liquity", "-a", "git-tellorflex-test-key", "--frozen-timeout", "asdf"])

    assert result.exception
    assert result.exit_code == 2

    expected = "Error: Invalid value for '-ft' / '--frozen-timeout': 'asdf' is not a valid integer."
    assert expected in result.stdout
