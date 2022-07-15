import getpass
import re
from typing import Any
from typing import Optional
from typing import Union

import click
from chained_accounts import find_accounts
from click.core import Context
from eth_utils import to_checksum_address
from telliot_core.cli.utils import async_run

from telliot_feed_examples.cli.utils import reporter_cli_core
from telliot_feed_examples.cli.utils import valid_diva_chain
from telliot_feed_examples.datafeed import DataFeed
from telliot_feed_examples.feeds import CATALOG_FEEDS, UNSET_FEEDS
from telliot_feed_examples.feeds.diva_protocol_feed import assemble_diva_datafeed
from telliot_feed_examples.feeds.tellor_rng_feed import assemble_rng_datafeed
from telliot_feed_examples.queries.query_catalog import query_catalog
from telliot_feed_examples.reporters.flashbot import FlashbotsReporter
from telliot_feed_examples.reporters.interval import IntervalReporter
from telliot_feed_examples.reporters.rng_interval import RNGReporter
from telliot_feed_examples.reporters.tellorflex import TellorFlexReporter
from telliot_feed_examples.utils.log import get_logger


logger = get_logger(__name__)


TELLOR_FLEX_CHAINS = (137, 122, 80001, 3, 69, 1666600000, 1666700000, 421611)


def get_stake_amount() -> float:
    """Retrieve desired stake amount from user

    Each stake is 10 TRB on TellorFlex Polygon. If an address
    is not staked for any reason, the TellorFlexReporter will attempt
    to stake. Number of stakes determines the reporter lock:

    reporter_lock = 12hrs / N * stakes

    Retrieves desidred stake amount from user input."""

    msg = "Enter amount TRB to stake if unstaked:"
    stake = click.prompt(msg, type=float, default=10.0, show_default=True)
    assert isinstance(stake, float)
    assert stake >= 10.0

    return stake


def parse_profit_input(expected_profit: str) -> Optional[Union[str, float]]:
    """Parses user input expected profit and ensures
    the input is either a float or the string 'YOLO'."""
    if expected_profit == "YOLO":
        return expected_profit
    else:
        try:
            return float(expected_profit)
        except ValueError:
            click.echo("Not a valid profit input. Enter float or the string, 'YOLO'")
            return None


def print_reporter_settings(
    signature_address: str,
    query_tag: str,
    gas_limit: int,
    priority_fee: Optional[int],
    expected_profit: str,
    chain_id: int,
    max_fee: Optional[int],
    transaction_type: int,
    legacy_gas_price: Optional[int],
    gas_price_speed: str,
    diva_pool_id: Optional[int],
    rng_timestamp: Optional[int],
) -> None:
    """Print user settings to console."""
    click.echo("")

    if signature_address != "":
        click.echo("⚡🤖⚡ Reporting through Flashbots relay ⚡🤖⚡")
        click.echo(f"Signature account: {signature_address}")

    if query_tag:
        click.echo(f"Reporting query tag: {query_tag}")
    elif diva_pool_id is not None:
        click.echo(f"Reporting data for Diva Protocol Pool ID {diva_pool_id}")
    else:
        click.echo("Reporting with synchronized queries")

    click.echo(f"Current chain ID: {chain_id}")

    if expected_profit == "YOLO":
        click.echo("🍜🍜🍜 Reporter not enforcing profit threshold! 🍜🍜🍜")
    else:
        click.echo(f"Expected percent profit: {expected_profit}%")

    click.echo(f"Transaction type: {transaction_type}")
    click.echo(f"Gas Limit: {gas_limit}")
    click.echo(f"Legacy gas price (gwei): {legacy_gas_price}")
    click.echo(f"Max fee (gwei): {max_fee}")
    click.echo(f"Priority fee (gwei): {priority_fee}")
    click.echo(f"Gas price speed: {gas_price_speed}\n")


def build_feed_from_input() -> Optional[DataFeed[Any]]:
    """
    Build a DataFeed from CLI input
    """
    try:
        query_type = input("Enter a valid Query Type: ").lower()
        query_type = re.sub('[^A-Za-z0-9]+', '', query_type)
        feed = UNSET_FEEDS[query_type]
    except KeyError:
        click.echo(f"No corresponding datafeed found for Query Type: {query_type}\n")
        return None
    try:
        for query_param in feed.query.__dict__.keys():
            # accessing the datatype
            param_dtype = feed.query.__annotations__[query_param]
            val = input(f"Enter value for Query Parameter {query_param}: ")

            if val is not None:
                # cast input from string to datatype of query parameter
                val = param_dtype(val)
                setattr(feed.query, query_param, val)
                setattr(feed.source, query_param, val)

            else:
                click.echo(f"Must set QueryParameter {query_param} of QueryType {query_type}")
                return None

        return feed

    except ValueError:
        click.echo(f"Value {val} for Query Parameter {query_param} does not match type {param_dtype}")
        return None


@click.group()
def reporter() -> None:
    """Report data on-chain."""
    pass

@reporter.command()
@click.option(
    "--build-feed",
    "-b",
    "build_feed",
    help="build a datafeed from a query type and query parameters",
    is_flag=True
)
@click.option(
    "--query-tag",
    "-qt",
    "query_tag",
    help="select datafeed using query tag",
    required=False,
    nargs=1,
    type=click.Choice([q.tag for q in query_catalog.find()]),
)
@click.option(
    "--gas-limit",
    "-gl",
    "gas_limit",
    help="use custom gas limit",
    nargs=1,
    type=int,
    default=350000,
)
@click.option(
    "--max-fee",
    "-mf",
    "max_fee",
    help="use custom maxFeePerGas (gwei)",
    nargs=1,
    type=int,
    required=False,
)
@click.option(
    "--priority-fee",
    "-pf",
    "priority_fee",
    help="use custom maxPriorityFeePerGas (gwei)",
    nargs=1,
    type=int,
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
    type=str,
    default="100.0",
)
@click.option(
    "--tx-type",
    "-tx",
    "tx_type",
    help="choose transaction type (0 for legacy txs, 2 for EIP-1559)",
    type=int,
    default=0,
)
@click.option(
    "--gas-price-speed",
    "-gps",
    "gas_price_speed",
    help="gas price speed for eth gas station API",
    nargs=1,
    type=click.Choice(
        ["safeLow", "average", "fast", "fastest"],
        case_sensitive=True,
    ),
    default="fast",
)
@click.option(
    "--pool-id",
    "-pid",
    "diva_pool_id",
    help="pool ID for Diva Protocol on Polygon",
    nargs=1,
    type=int,
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
    "--rng-timestamp",
    "-rngts",
    "rng_timestamp",
    help="timestamp for Tellor RNG",
    nargs=1,
    type=int,
)
@click.option("--rng-auto/--rng-auto-off", default=False)
@click.option("--submit-once/--submit-continuous", default=False)
@click.option("-pwd", "--password", type=str)
@click.option("-spwd", "--signature-password", type=str)
@click.pass_context
@async_run
async def report(
    ctx: Context,
    query_tag: str,
    build_feed: bool,
    tx_type: int,
    gas_limit: int,
    max_fee: Optional[int],
    priority_fee: Optional[int],
    legacy_gas_price: Optional[int],
    expected_profit: str,
    submit_once: bool,
    wait_period: int,
    gas_price_speed: str,
    diva_pool_id: int,
    rng_timestamp: int,
    password: str,
    signature_password: str,
    rng_auto: bool,
) -> None:
    """Report values to Tellor oracle"""
    # Ensure valid user input for expected profit
    expected_profit = parse_profit_input(expected_profit)  # type: ignore
    if expected_profit is None:
        return

    assert tx_type in (0, 2)

    name = ctx.obj["ACCOUNT_NAME"]
    sig_acct_name = ctx.obj["SIGNATURE_ACCOUNT_NAME"]

    try:
        if not password:
            password = getpass.getpass(f"Enter password for {name} keyfile: ")
    except ValueError:
        click.echo("Invalid Password")

    if sig_acct_name is not None:
        try:
            if not signature_password:
                signature_password = getpass.getpass(f"Enter password for {sig_acct_name} keyfile: ")
        except ValueError:
            click.echo("Invalid Password")

    # Initialize telliot core app using CLI context
    async with reporter_cli_core(ctx) as core:

        # Make sure current account is unlocked
        account = core.get_account()
        if not account.is_unlocked:
            account.unlock(password)

        if sig_acct_name is not None:
            sig_account = find_accounts(name=sig_acct_name)[0]
            if not sig_account.is_unlocked:
                sig_account.unlock(password)
            sig_acct_addr = to_checksum_address(sig_account.address)
        else:
            sig_acct_addr = ""  # type: ignore

        cid = core.config.main.chain_id

        # If we need to build a datafeed
        if build_feed:
            chosen_feed = build_feed_from_input()  # type: ignore

            if chosen_feed is None:
                click.echo("")
                return

        # Use selected feed, or choose automatically
        if query_tag is not None:
            try:
                chosen_feed: DataFeed[Any] = CATALOG_FEEDS[query_tag]  # type: ignore
            except KeyError:
                click.echo(f"No corresponding datafeed found for Query Type: {query_tag}\n")
                return
        elif diva_pool_id is not None:
            if not valid_diva_chain(chain_id=cid):
                click.echo("Diva Protocol not supported for this chain")
                return
            # Generate datafeed
            chosen_feed = await assemble_diva_datafeed(pool_id=diva_pool_id, node=core.endpoint, account=account)
            if chosen_feed is None:
                click.echo("DIVA Protocol datafeed generation failed")
                return
        elif rng_timestamp is not None:
            chosen_feed = await assemble_rng_datafeed(timestamp=rng_timestamp, node=core.endpoint, account=account)
        else:
            chosen_feed = None

        print_reporter_settings(
            signature_address=sig_acct_addr,
            query_tag=query_tag,
            transaction_type=tx_type,
            gas_limit=gas_limit,
            max_fee=max_fee,
            priority_fee=priority_fee,
            legacy_gas_price=legacy_gas_price,
            expected_profit=expected_profit,
            chain_id=cid,
            gas_price_speed=gas_price_speed,
            diva_pool_id=diva_pool_id,
            rng_timestamp=rng_timestamp,
        )

        _ = input("Press [ENTER] to confirm settings.")

        common_reporter_kwargs = {
            "endpoint": core.endpoint,
            "account": account,
            "datafeed": chosen_feed,
            "transaction_type": tx_type,
            "gas_limit": gas_limit,
            "max_fee": max_fee,
            "priority_fee": priority_fee,
            "legacy_gas_price": legacy_gas_price,
            "gas_price_speed": gas_price_speed,
            "chain_id": cid,
        }

        # Report to Polygon TellorFlex
        if core.config.main.chain_id in TELLOR_FLEX_CHAINS:
            stake = get_stake_amount()

            tellorflex = core.get_tellorflex_contracts()

            # Type 2 transactions unsupported currently
            common_reporter_kwargs["transaction_type"] = 0

            if rng_auto:
                reporter = RNGReporter(
                    oracle=tellorflex.oracle,
                    token=tellorflex.token,
                    autopay=tellorflex.autopay,
                    stake=stake,
                    expected_profit=expected_profit,
                    wait_period=120,
                    **common_reporter_kwargs,
                )
            else:
                reporter = TellorFlexReporter(
                    oracle=tellorflex.oracle,
                    token=tellorflex.token,
                    autopay=tellorflex.autopay,
                    stake=stake,
                    expected_profit=expected_profit,
                    wait_period=wait_period,
                    **common_reporter_kwargs,
                )  # type: ignore
        # Report to TellorX
        else:
            tellorx = core.get_tellorx_contracts()
            tellorx_reporter_kwargs = {
                "master": tellorx.master,
                "oracle": tellorx.oracle,
                "expected_profit": expected_profit,
                **common_reporter_kwargs,
            }

            if sig_acct_addr != "":
                reporter = FlashbotsReporter(
                    **tellorx_reporter_kwargs,
                    signature_account=sig_account,
                )  # type: ignore
            else:
                reporter = IntervalReporter(**tellorx_reporter_kwargs)  # type: ignore

        if submit_once:
            _, _ = await reporter.report_once()
        else:
            _, _ = await reporter.report()
