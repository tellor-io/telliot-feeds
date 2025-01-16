from typing import Any
from typing import Optional

import click
from click.core import Context
from telliot_core.cli.utils import async_run

from telliot_feeds.cli.utils import build_feed_from_input
from telliot_feeds.cli.utils import common_options
from telliot_feeds.cli.utils import common_reporter_options
from telliot_feeds.cli.utils import get_accounts_from_name
from telliot_feeds.cli.utils import reporter_cli_core
from telliot_feeds.datafeed import DataFeed
from telliot_feeds.feeds import CATALOG_FEEDS
from telliot_feeds.reporters.layer.layer_reporter import LayerReporter  # type: ignore
from telliot_feeds.utils.cfg import check_endpoint
from telliot_feeds.utils.cfg import setup_config
from telliot_feeds.utils.log import get_logger


logger = get_logger(__name__)


@click.group()
def reporter() -> None:
    """Report data on-chain."""
    pass


@reporter.command()
@common_options
@common_reporter_options
@click.option(
    "--build-feed",
    "-b",
    "build_feed",
    help="build a datafeed from a query type and query parameters",
    is_flag=True,
)
@click.pass_context
@async_run
async def layer(
    ctx: Context,
    query_tag: str,
    build_feed: bool,
    tx_type: int,
    gas_limit: int,
    base_fee_per_gas: Optional[float],
    priority_fee_per_gas: Optional[float],
    max_fee_per_gas: Optional[float],
    legacy_gas_price: Optional[int],
    expected_profit: str,
    submit_once: bool,
    wait_period: int,
    password: str,
    min_native_token_balance: float,
    stake: float,
    account_str: str,
    check_rewards: bool,
    gas_multiplier: int,
    max_priority_fee_range: int,
    unsafe: bool,
    skip_manual_feeds: bool,
) -> None:
    """Report values to Layer"""
    ctx.obj["ACCOUNT_NAME"] = account_str

    accounts = get_accounts_from_name(account_str)
    if not accounts:
        return
    print(accounts)
    print(accounts[0].chains[0])
    ctx.obj["CHAIN_ID"] = accounts[0].chains[0]  # used in reporter_cli_core
    # Initialize telliot core app using CLI context
    async with reporter_cli_core(ctx) as core:
        print(account_str)
        core._config, account = setup_config(core.config, account_name=account_str, unsafe=False)

        endpoint = check_endpoint(core._config)
        print(endpoint, "endpoint")
        if not endpoint or not account:
            click.echo("Accounts and/or endpoint unset.")
            click.echo(f"Account: {account}")
            click.echo(f"Endpoint: {core._config.get_endpoint()}")
            return

        # Make sure current account is unlocked
        if not account.is_unlocked:
            account.unlock(password)

        # If we need to build a datafeed
        if build_feed:
            chosen_feed = build_feed_from_input()

            if chosen_feed is None:
                click.echo("Unable to build Datafeed from provided input")
                return

        # Use selected feed, or choose automatically
        elif query_tag is not None:
            try:
                chosen_feed: DataFeed[Any] = CATALOG_FEEDS[query_tag]  # type: ignore
            except KeyError:
                click.echo(f"No corresponding datafeed found for query tag: {query_tag}\n")
                return

        if not unsafe:
            _ = input("Press [ENTER] to confirm settings.")

        reporter = LayerReporter(endpoint=endpoint, account=account, wait_period=wait_period)
        if submit_once:
            _, _ = await reporter.report_once()
        else:
            await reporter.report()
