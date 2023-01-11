""" Telliot CLI

A simple interface for interacting with telliot_feeds's functionality.
Configure telliot_feeds's settings via this interface's command line flags
or in the configuration file.
"""
import click
from click.core import Context

from telliot_feeds.cli.commands.account import account
from telliot_feeds.cli.commands.catalog import catalog
from telliot_feeds.cli.commands.config import config
from telliot_feeds.cli.commands.integrations import integrations
from telliot_feeds.cli.commands.query import query
from telliot_feeds.cli.commands.report import report
from telliot_feeds.cli.commands.settle import settle
from telliot_feeds.utils.log import get_logger


logger = get_logger(__name__)


@click.group()
@click.option(
    "--test-config",
    is_flag=True,
    help="Runs command with test configuration (developer use only)",
)
@click.pass_context
def main(
    ctx: Context,
    test_config: bool,
) -> None:
    """Telliot command line interface"""
    ctx.ensure_object(dict)
    ctx.obj["TEST_CONFIG"] = test_config


main.add_command(report)
main.add_command(query)
main.add_command(catalog)
main.add_command(settle)
main.add_command(integrations)
main.add_command(config)
main.add_command(account)

if __name__ == "__main__":
    main()
