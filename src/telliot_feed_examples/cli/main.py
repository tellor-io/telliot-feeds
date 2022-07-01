""" Telliot CLI

A simple interface for interacting with telliot_feeds's functionality.
Configure telliot_feeds's settings via this interface's command line flags
or in the configuration file.
"""
import click
from click.core import Context

from chained_accounts import find_accounts

from telliot_feed_examples.cli.commands.report import report
from telliot_feed_examples.cli.commands.tip import tip
from telliot_feed_examples.cli.commands.settle import settle
from telliot_feed_examples.cli.commands.catalog import catalog
from telliot_feed_examples.cli.commands.query import query


@click.group()
@click.option(
    "--account",
    "-a",
    "account",
    help="Name of account used for reporting.",
    required=False,
    nargs=1,
    type=str,
)
@click.option(
    "--signature-account",
    "-sa",
    "signature_account",
    help="Name of signature account used for reporting with Flashbots.",
    required=False,
    nargs=1,
    type=str,
)
@click.option(
    "--test_config",
    is_flag=True,
    help="Runs command with test configuration (developer use only)",
)
@click.pass_context
def cli(
    ctx: Context,
    account: str,
    signature_account: str,
    test_config: bool,
) -> None:
    """Telliot command line interface"""
    ctx.ensure_object(dict)
    ctx.obj["ACCOUNT_NAME"] = account
    ctx.obj["SIGNATURE_ACCOUNT_NAME"] = signature_account
    ctx.obj["TEST_CONFIG"] = test_config

    # Pull chain from account
    # Note: this is not be reliable because accounts can be associated with
    # multiple chains.
    accounts = find_accounts(name=account)
    ctx.obj["CHAIN_ID"] = accounts[0].chains[0]


cli.add_command(report)
cli.add_command(tip)
cli.add_command(query)
cli.add_command(catalog)
cli.add_command(settle)

if __name__ == "__main__":
    cli()
