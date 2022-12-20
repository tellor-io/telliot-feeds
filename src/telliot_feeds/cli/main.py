""" Telliot CLI

A simple interface for interacting with telliot_feeds's functionality.
Configure telliot_feeds's settings via this interface's command line flags
or in the configuration file.
"""
import click
from chained_accounts import find_accounts
from click.core import Context

from telliot_feeds.cli.commands.account import account
from telliot_feeds.cli.commands.catalog import catalog
from telliot_feeds.cli.commands.config import config
from telliot_feeds.cli.commands.integrations import integrations
from telliot_feeds.cli.commands.query import query
from telliot_feeds.cli.commands.report import report
from telliot_feeds.cli.commands.settle import settle

# from telliot_feeds.cli.commands.tip import tip


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
    "--test-config",
    is_flag=True,
    help="Runs command with test configuration (developer use only)",
)
@click.pass_context
def main(
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


main.add_command(report)
# main.add_command(tip)
main.add_command(query)
main.add_command(catalog)
main.add_command(settle)
main.add_command(integrations)
main.add_command(config)
main.add_command(account)

if __name__ == "__main__":
    main()
