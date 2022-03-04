""" Telliot Feed Examples CLI

A simple interface for interacting with telliot example feed functionality.
"""
import asyncio
import getpass
from typing import Optional
from typing import Union

import click
from chained_accounts import find_accounts
from click.core import Context
from eth_utils import to_checksum_address
from telliot_core.apps.core import TelliotCore
from telliot_core.cli.utils import async_run
from telliot_core.cli.utils import cli_core
from telliot_core.data.query_catalog import query_catalog
from telliot_core.tellor.tellorflex.diva import DivaOracleTellorContract

from telliot_feed_examples.feeds import CATALOG_FEEDS
from telliot_feed_examples.feeds.diva_protocol_feed import assemble_diva_datafeed
from telliot_feed_examples.reporters.flashbot import FlashbotsReporter
from telliot_feed_examples.reporters.interval import IntervalReporter
from telliot_feed_examples.reporters.tellorflex import PolygonReporter
from telliot_feed_examples.utils.log import get_logger
from telliot_feed_examples.utils.oracle_write import tip_query


logger = get_logger(__name__)

TELLOR_FLEX_CHAINS = (137, 80001, 3, 122)
DIVA_PROTOCOL_CHAINS = (137, 80001, 3)


def get_stake_amount() -> float:
    """Retrieve desired stake amount from user

    Each stake is 10 TRB on TellorFlex Polygon. If an address
    is not staked for any reason, the PolygonReporter will attempt
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


def valid_diva_chain(chain_id: int) -> bool:
    """Ensure given chain ID supports reporting Diva Protocol data."""
    if chain_id not in DIVA_PROTOCOL_CHAINS:
        print(
            f"Current chain id ({chain_id}) not supported for"
            " reporting Diva Protocol data."
        )
        return False
    return True


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


def reporter_cli_core(ctx: click.Context) -> TelliotCore:
    """Get telliot core configured in reporter CLI context"""
    # Delegate to main cli core getter
    # (handles ACCOUNT_NAME, CHAIN_ID, and TEST_CONFIG)
    core = cli_core(ctx)

    # Ensure chain id compatible with flashbots relay
    if ctx.obj["SIGNATURE_ACCOUNT_NAME"] is not None:
        # Only supports mainnet
        assert core.config.main.chain_id == 1

    assert core.config

    return core


# Main CLI options
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


# Report subcommand options
@cli.command()
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
@click.option("--submit-once/--submit-continuous", default=False)
@click.option("-pwd", "--password", type=str)
@click.option("-spwd", "--signature-password", type=str)
@click.pass_context
@async_run
async def report(
    ctx: Context,
    query_tag: str,
    tx_type: int,
    gas_limit: int,
    max_fee: Optional[int],
    priority_fee: Optional[int],
    legacy_gas_price: Optional[int],
    expected_profit: str,
    submit_once: bool,
    gas_price_speed: str,
    diva_pool_id: int,
    password: str,
    signature_password: str,
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
                signature_password = getpass.getpass(
                    f"Enter password for {sig_acct_name} keyfile: "
                )
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

        # Use selected feed, or choose automatically
        if query_tag is not None:
            chosen_feed = CATALOG_FEEDS[query_tag]
        elif diva_pool_id is not None:
            if not valid_diva_chain(chain_id=cid):
                return
            # Generate datafeed
            chosen_feed = await assemble_diva_datafeed(
                pool_id=diva_pool_id, node=core.endpoint, account=account
            )
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

            reporter = PolygonReporter(
                oracle=tellorflex.oracle,
                token=tellorflex.token,
                stake=stake,
                **common_reporter_kwargs,
            )
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


@cli.command()
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
    "--amount-trb",
    "-trb",
    "amount_trb",
    help="amount to tip in TRB for a query ID",
    nargs=1,
    type=float,
    required=True,
)
@click.pass_context
@async_run
async def tip(
    ctx: Context,
    query_tag: str,
    amount_trb: float,
) -> None:
    """Tip TRB for a selected query ID"""

    # Initialize telliot core app using CLI context
    async with reporter_cli_core(ctx) as core:

        click.echo(f"Tipping {amount_trb} TRB for query tag: {query_tag}.")

        chosen_feed = CATALOG_FEEDS[query_tag]
        tip = int(amount_trb * 1e18)

        tellorx = core.get_tellorx_contracts()
        tx_receipt, status = asyncio.run(
            tip_query(
                oracle=tellorx.oracle,
                datafeed=chosen_feed,
                tip=tip,
            )
        )

        if status.ok and not status.error and tx_receipt:
            click.echo("Success!")
            tx_hash = tx_receipt["transactionHash"].hex()
            # Point to relevant explorer
            logger.info(f"View tip: \n{core.endpoint.explorer}/tx/{tx_hash}")
        else:
            logger.error(status)


@cli.command()
@click.option(
    "--pool-id",
    "-pid",
    "pool_id",
    help="pool ID for Diva Protocol on Polygon",
    nargs=1,
    type=int,
    required=True,
)
@click.option(
    "--gas-price",
    "-gp",
    "legacy_gas_price",
    help="use custom legacy gasPrice (gwei)",
    nargs=1,
    type=int,
    required=False,
    default=100,
)
@click.option("-pswd", "--password", type=str)
@click.pass_context
@async_run
async def settle(
    ctx: Context,
    pool_id: int,
    password: str,
    legacy_gas_price: int = 100,
) -> None:
    """Settle a derivative pool in DIVA Protocol."""

    name = ctx.obj["ACCOUNT_NAME"]
    try:
        if not password:
            password = getpass.getpass(f"Enter password for {name} keyfile: ")
    except ValueError:
        click.echo("Invalid Password")

    # Initialize telliot core app using CLI context
    async with reporter_cli_core(ctx) as core:

        # Make sure current account is unlocked
        account = core.get_account()
        if not account.is_unlocked:
            account.unlock(password)

        cid = core.config.main.chain_id
        if not valid_diva_chain(chain_id=cid):
            return

        oracle = DivaOracleTellorContract(core.endpoint, account)
        oracle.connect()

        status = await oracle.set_final_reference_value(
            pool_id=pool_id, legacy_gas_price=legacy_gas_price
        )
        if status is not None and status.ok:
            click.echo(f"Pool {pool_id} settled.")
        else:
            click.echo(f"Unable to settle Pool {pool_id}.")


if __name__ == "__main__":
    cli()
