from typing import Optional

import click
from click.core import Context
from telliot_core.cli.utils import async_run
from web3 import Web3

from telliot_feeds.cli.utils import common_options
from telliot_feeds.cli.utils import common_reporter_options
from telliot_feeds.cli.utils import get_accounts_from_name
from telliot_feeds.cli.utils import reporter_cli_core
from telliot_feeds.feeds import CATALOG_FEEDS
from telliot_feeds.reporters.customized import ChainLinkFeeds
from telliot_feeds.reporters.customized.backup_reporter import ChainlinkBackupReporter
from telliot_feeds.utils.cfg import check_endpoint
from telliot_feeds.utils.cfg import setup_config
from telliot_feeds.utils.log import get_logger

logger = get_logger(__name__)


@click.group()
def liquity_reporter() -> None:
    """Report data on-chain."""
    pass


@liquity_reporter.command()
@common_options
@common_reporter_options
@click.option(
    "-clf",
    "--chainlink-feed",
    nargs=1,
)
@click.option("-pc", "--percent-change", type=float, default=0.5)
@click.option("-ft", "--frozen-timeout", type=int, default=14400)
@click.pass_context
@async_run
async def liquity(
    ctx: Context,
    tx_type: int,
    gas_limit: int,
    max_fee_per_gas: Optional[float],
    priority_fee_per_gas: Optional[float],
    base_fee_per_gas: Optional[float],
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
    percent_change: float,
    frozen_timeout: int,
    query_tag: str,
    chainlink_feed: str,
    unsafe: bool,
    skip_manual_feeds: bool,
) -> None:
    """Report values to Tellor oracle if certain conditions are met."""
    click.echo("Starting Liquity Backup Reporter...")
    ctx.obj["ACCOUNT_NAME"] = account_str
    ctx.obj["SIGNATURE_ACCOUNT_NAME"] = None
    if query_tag is None:
        query_tag = "eth-usd-spot"
    datafeed = CATALOG_FEEDS.get(query_tag)
    if datafeed is None:
        raise click.UsageError(f"Invalid query tag: {query_tag}, enter a valid query tag with API support, use --help")

    accounts = get_accounts_from_name(account_str)
    if not accounts:
        return
    chain_id = accounts[0].chains[0]
    if chainlink_feed is None:
        chainlink_feed = ChainLinkFeeds.get(chain_id)
        if chainlink_feed is None:
            raise click.UsageError(f"Chain link feed not found for chain id: {chain_id}")
    else:
        try:
            chainlink_feed = Web3.to_checksum_address(chainlink_feed)
        except ValueError:
            raise click.UsageError("Invalid chain link feed address")

    ctx.obj["CHAIN_ID"] = chain_id  # used in reporter_cli_core
    # Initialize telliot core app using CLI context
    async with reporter_cli_core(ctx) as core:

        core._config, account = setup_config(core.config, account_name=account_str, unsafe=unsafe)

        endpoint = check_endpoint(core._config)

        if not endpoint or not account:
            click.echo("Accounts and/or endpoint unset.")
            click.echo(f"Account: {account}")
            click.echo(f"Endpoint: {core._config.get_endpoint()}")
            return

        # Make sure current account is unlocked
        if not account.is_unlocked:
            account.unlock(password)

        click.echo("Reporter settings:")
        click.echo(f"Max tolerated price change: {percent_change * 100}%")
        click.echo(f"Value considered stale after: {frozen_timeout} seconds")
        click.echo(f"Transaction type: {tx_type}")
        click.echo(f"Gas Limit: {gas_limit}")
        click.echo(f"Legacy gas price (gwei): {legacy_gas_price}")
        click.echo(f"Max fee (gwei): {max_fee_per_gas}")
        click.echo(f"Priority fee (gwei): {priority_fee_per_gas}")
        click.echo(f"Desired stake amount: {stake}")
        click.echo(f"Minimum native token balance (e.g. ETH if on Ethereum mainnet): {min_native_token_balance}")
        click.echo("\n")

        _ = input("Press [ENTER] to confirm settings.")

        contracts = core.get_tellor360_contracts()

        common_reporter_kwargs = {
            "endpoint": core.endpoint,
            "account": account,
            "datafeed": datafeed,
            "gas_limit": gas_limit,
            "max_fee_per_gas": max_fee_per_gas,
            "priority_fee_per_gas": priority_fee_per_gas,
            "base_fee_per_gas": base_fee_per_gas,
            "legacy_gas_price": legacy_gas_price,
            "chain_id": core.config.main.chain_id,
            "wait_period": wait_period,
            "oracle": contracts.oracle,
            "autopay": contracts.autopay,
            "token": contracts.token,
            "expected_profit": expected_profit,
            "stake": stake,
            "transaction_type": tx_type,
            "min_native_token_balance": int(min_native_token_balance * 10**18),
            "check_rewards": check_rewards,
            "gas_multiplier": gas_multiplier,
            "max_priority_fee_range": max_priority_fee_range,
            "skip_manual_feeds": skip_manual_feeds,
        }

        reporter = ChainlinkBackupReporter(
            chainlink_is_frozen_timeout=frozen_timeout,
            chainlink_max_price_change=percent_change,
            chainlink_feed=chainlink_feed,
            **common_reporter_kwargs,
        )

        if submit_once:
            reporter.wait_period = 0
            await reporter.report(report_count=1)
        else:
            await reporter.report()
