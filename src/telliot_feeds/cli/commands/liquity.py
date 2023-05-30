from typing import Optional

import click
from click.core import Context
from telliot_core.cli.utils import async_run
from web3 import Web3

from telliot_feeds.cli.constants import REWARDS_CHECK_MESSAGE
from telliot_feeds.cli.constants import STAKE_MESSAGE
from telliot_feeds.cli.utils import get_accounts_from_name
from telliot_feeds.cli.utils import parse_profit_input
from telliot_feeds.cli.utils import reporter_cli_core
from telliot_feeds.cli.utils import valid_transaction_type
from telliot_feeds.feeds import CATALOG_FEEDS
from telliot_feeds.queries.query_catalog import query_catalog
from telliot_feeds.reporters.customized import ChainLinkFeeds
from telliot_feeds.reporters.customized.backup_reporter import BackupReporter
from telliot_feeds.utils.cfg import check_endpoint
from telliot_feeds.utils.cfg import setup_config
from telliot_feeds.utils.log import get_logger

logger = get_logger(__name__)


@click.group()
def liquity_reporter() -> None:
    """Report data on-chain."""
    pass


@click.option(
    "--account",
    "-a",
    "account_str",
    help="Name of account used for reporting, staking, etc. More info: run `telliot account --help`",
    required=True,
    nargs=1,
    type=str,
)
@liquity_reporter.command()
@click.option(
    "--gas-limit",
    "-gl",
    "gas_limit",
    help="use custom gas limit",
    nargs=1,
    type=int,
)
@click.option(
    "--max-fee",
    "-mf",
    "max_fee",
    help="use custom maxFeePerGas (gwei)",
    nargs=1,
    type=float,
    required=False,
)
@click.option(
    "--priority-fee",
    "-pf",
    "priority_fee",
    help="use custom maxPriorityFeePerGas (gwei)",
    nargs=1,
    type=float,
    required=False,
)
@click.option(
    "--gas-price",
    "-gp",
    "legacy_gas_price",
    help="use custom legacy gasPrice (gwei)",
    nargs=1,
    type=int,
    required=False,
)
@click.option(
    "--profit",
    "-p",
    "expected_profit",
    help="lower threshold (inclusive) for expected percent profit",
    nargs=1,
    # User can omit profitability checks by specifying "YOLO"
    type=click.UNPROCESSED,
    required=False,
    callback=parse_profit_input,
    default="100.0",
)
@click.option(
    "--tx-type",
    "-tx",
    "tx_type",
    help="choose transaction type (0 for legacy txs, 2 for EIP-1559)",
    type=click.UNPROCESSED,
    required=False,
    callback=valid_transaction_type,
    default=2,
)
@click.option(
    "-wp",
    "--wait-period",
    help="wait period between feed suggestion calls",
    nargs=1,
    type=int,
    default=7,
)
@click.option(
    "--stake",
    "-s",
    "stake",
    help=STAKE_MESSAGE,
    nargs=1,
    type=float,
    default=10.0,
)
@click.option(
    "--min-native-token-balance",
    "-mnb",
    "min_native_token_balance",
    help="Minimum native token balance required to report. Denominated in ether.",
    nargs=1,
    type=float,
    default=0.25,
)
@click.option(
    "--check-rewards/--no-check-rewards",
    "-cr/-ncr",
    "check_rewards",
    default=True,
    help=REWARDS_CHECK_MESSAGE,
)
@click.option(
    "--gas-multiplier",
    "-gm",
    "gas_multiplier",
    help="increase gas price by this percentage (default 1%) ie 5 = 5%",
    nargs=1,
    type=int,
    default=1,  # 1% above the gas price by web3
)
@click.option(
    "--max-priority-fee-range",
    "-mpfr",
    "max_priority_fee_range",
    help="the maximum range of priority fees to use in gwei (default 80 gwei)",
    nargs=1,
    type=int,
    default=80,  # 80 gwei
)
@click.option(
    "--query-tag",
    "-qt",
    "query_tag",
    help="select datafeed using query tag",
    required=False,
    nargs=1,
    default="eth-usd-spot",
    type=click.Choice([q.tag for q in query_catalog.find()]),
)
@click.option(
    "-clf",
    "--chainlink-feed",
    nargs=1,
)
@click.option("--submit-once/--submit-continuous", default=False)
@click.option("-pwd", "--password", type=str)
@click.option("-pd", "--price-deviation", type=float, default=0.5)
@click.option("-ft", "--frozen-timeout", type=int, default=3600)
@click.pass_context
@async_run
async def liquity(
    ctx: Context,
    tx_type: int,
    gas_limit: int,
    max_fee: Optional[float],
    priority_fee: Optional[float],
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
    price_deviation: float,
    frozen_timeout: int,
    query_tag: str,
    chainlink_feed: str,
) -> None:
    """Report values to Tellor oracle if certain conditions are met."""
    click.echo("Starting Liquity Backup Reporter...")
    ctx.obj["ACCOUNT_NAME"] = account_str
    ctx.obj["SIGNATURE_ACCOUNT_NAME"] = None
    if query_tag != "eth-usd-spot" and chainlink_feed is None:
        raise click.UsageError("Must specify chain link feed if not using eth-usd-spot")
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
            raise click.UsageError("Chain link feed not found for chain id: {chain_id}")
    else:
        try:
            chainlink_feed = Web3.toChecksumAddress(chainlink_feed)
        except ValueError:
            raise click.UsageError("Invalid chain link feed address")

    ctx.obj["CHAIN_ID"] = chain_id  # used in reporter_cli_core
    # if max_fee flag is set, then priority_fee must also be set
    if (max_fee is not None and priority_fee is None) or (max_fee is None and priority_fee is not None):
        raise click.UsageError("Must specify both max fee and priority fee")
    # Initialize telliot core app using CLI context
    async with reporter_cli_core(ctx) as core:

        core._config, account = setup_config(core.config, account_name=account_str)

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
        click.echo(f"Max tolerated price change: {price_deviation * 100}%")
        click.echo(f"Value considered stale after: {frozen_timeout} seconds")
        click.echo(f"Transaction type: {tx_type}")
        click.echo(f"Gas Limit: {gas_limit}")
        click.echo(f"Legacy gas price (gwei): {legacy_gas_price}")
        click.echo(f"Max fee (gwei): {max_fee}")
        click.echo(f"Priority fee (gwei): {priority_fee}")
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
            "max_fee": max_fee,
            "priority_fee": priority_fee,
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
        }

        reporter = BackupReporter(
            chainlink_is_frozen_timeout=frozen_timeout,
            chainlink_max_price_deviation=price_deviation,
            chainlink_feed=chainlink_feed,
            **common_reporter_kwargs,
        )

        if submit_once:
            reporter.wait_period = 0
            await reporter.report(report_count=1)
        else:
            await reporter.report()
