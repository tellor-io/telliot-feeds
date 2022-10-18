from click.testing import CliRunner

from telliot_feeds.cli.main import main as cli_main


def test_help():
    runner = CliRunner()
    result = runner.invoke(cli_main, ["query", "--help"])

    assert "decode" in result.stdout


def test_decode_query_data():
    """Test user choosing to use different staker."""
    query_data = (
        "0x00000000000000000000000000000000000000000000000000"
        "0000000000004000000000000000000000000000000000000000"
        "0000000000000000000000008000000000000000000000000000"
        "0000000000000000000000000000000000000954656c6c6f7252"
        "4e47000000000000000000000000000000000000000000000000"
        "0000000000000000000000000000000000000000000000000000"
        "0000000020000000000000000000000000000000000000000000"
        "0000000000000062ebc2d0"
    )
    runner = CliRunner()
    result = runner.invoke(cli_main, ["query", "decode", "-qd", query_data])

    assert "TellorRNG(timestamp=1659618000)" in result.output


def test_decode_query_data_fail():
    runner = CliRunner()
    result = runner.invoke(cli_main, ["query", "decode", "-qd", "invalidquerydata"])

    assert "Invalid query data" in result.output


def test_decode_submit_val_bytes():
    submitted_val_bytes = "0x00000000000000000000000000000000000000000000000180b1392215d3fb8f"
    runner = CliRunner()
    result = runner.invoke(
        cli_main, ["query", "decode", "-svb", submitted_val_bytes], input="1"  # User chooses SpotPrice
    )

    assert "Decoded value: 27.72" in result.output


def test_decode_submit_val_bytes_fail():
    submitted_val_bytes = "0x00000000000000000000000000000000000000000000000180b1392215d3fb8f"
    runner = CliRunner()
    result = runner.invoke(cli_main, ["query", "decode", "-svb", submitted_val_bytes], input="3")

    assert "Unable to decode value using query type: Snapshot" in result.output


def test_new_query():
    """Test building a new query instance from the CLI"""
    runner = CliRunner()
    result = runner.invoke(cli_main, ["query", "--help"])

    assert "new" in result.output
