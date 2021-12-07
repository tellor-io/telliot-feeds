""" Telliot Feed Examples CLI

A simple interface for interacting with telliot example feed functionality.
"""
import asyncio

import click
from click.core import Context
from telliot_core.apps.telliot_config import TelliotConfig

from telliot_feed_examples.feeds import LEGACY_DATAFEEDS
from telliot_feed_examples.reporters.interval import IntervalReporter
from telliot_feed_examples.utils.contract import get_tellor_contracts
from telliot_feed_examples.utils.log import get_logger
from telliot_feed_examples.utils.oracle_write import tip_query


logger = get_logger(__name__)


# Get default configs from ~/telliot/
cfg = TelliotConfig()


# Main CLI options
@click.group()
@click.option(
    "--private-key",  # flag option 1
    "-pk",  # flag option 2
    "private_key",  # variable name of user input
    help="override the config's private key",
    required=False,
    nargs=1,
    default=cfg.main.private_key,
    type=str,
)
@click.option(
    "--chain-id",
    "-cid",
    "chain_id",
    help="override the config's chain ID",
    required=False,
    nargs=1,
    default=cfg.main.chain_id,
    type=int,
)
@click.option(
    "--legacy-id",
    "-lid",
    "legacy_id",
    help="report to a legacy ID",
    required=True,
    nargs=1,
    type=str,
)
@click.option(
    "--gas-limit",
    "-gl",
    "gas_limit",
    help="use custom gas limit",
    nargs=1,
    type=int,
    default=500000,
)
@click.pass_context
def cli(
    ctx: Context, private_key: str, chain_id: int, legacy_id: str, gas_limit: int
) -> None:
    """Telliot command line interface"""
    # Ensure valid legacy id
    if legacy_id not in LEGACY_DATAFEEDS:
        click.echo(
            f"Invalid legacy ID. Valid choices: {', '.join(list(LEGACY_DATAFEEDS))}"
        )
        return

    ctx.ensure_object(dict)
    ctx.obj["PRIVATE_KEY"] = private_key
    ctx.obj["CHAIN_ID"] = chain_id
    ctx.obj["LEGACY_ID"] = legacy_id
    ctx.obj["GAS_LIMIT"] = gas_limit


# Report subcommand options
@cli.command()
@click.option(
    "--max-gas-price",
    "-mgp",
    "max_gas_price",
    help="maximum gas price used by eth gas station",
    nargs=1,
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
    "--gas-price",
    "-gp",
    "gas_price",
    help="use custom gas price (overrides eth gas station estimate)",
    nargs=1,
    type=int,
    required=False,
)
@click.option(
    "--profit",
    "-p",
    "profit_percent",
    help="lower threshold (inclusive) for expected percent profit",
    nargs=1,
    type=float,
    default=0.0,
)
@click.option("--submit-once/--submit-continuous", default=False)
@click.pass_context
def report(
    ctx: Context,
    gas_price: int,
    max_gas_price: int,
    gas_price_speed: str,
    submit_once: bool,
    profit_percent: float,
) -> None:
    """Report values to Tellor oracle"""

    private_key = ctx.obj["PRIVATE_KEY"]
    chain_id = ctx.obj["CHAIN_ID"]
    legacy_id = ctx.obj["LEGACY_ID"]
    gas_limit = ctx.obj["GAS_LIMIT"]
    cfg.main.private_key = private_key
    cfg.main.chain_id = chain_id

    endpoint = cfg.get_endpoint()

    # Print user settings to console
    click.echo(f"Reporting legacy ID: {legacy_id}")
    click.echo(f"Current chain ID: {chain_id}")

    if profit_percent == 0.0:
        click.echo("Reporter not enforcing profit threshold.")
    else:
        click.echo(f"Lower bound for expected percent profit: {profit_percent}%")

    # Gas price overrides other gas price settings
    if not gas_price:
        if max_gas_price != 0:
            click.echo(
                f"Reporter will use a maximum gas price of {max_gas_price} gwei."
            )
        click.echo(f"Selected gas price speed: {gas_price_speed}")
    else:
        click.echo(f"Gas price: {gas_price}")

    click.echo(f"Gas Limit: {gas_limit}")

    # return
    master, oracle = get_tellor_contracts(
        private_key=private_key, endpoint=endpoint, chain_id=chain_id
    )

    chosen_feed = LEGACY_DATAFEEDS[legacy_id]

    legacy_reporter = IntervalReporter(
        endpoint=endpoint,
        private_key=private_key,
        master=master,
        oracle=oracle,
        datafeed=chosen_feed,
        profit_threshold=profit_percent,
        gas_price=gas_price,
        max_gas_price=max_gas_price,
        gas_price_speed=gas_price_speed,
        gas_limit=gas_limit,
    )

    if submit_once:
        _, _ = asyncio.run(legacy_reporter.report_once())
    else:
        _, _ = asyncio.run(legacy_reporter.report())


@cli.command()
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
def tip(
    ctx: Context,
    amount_trb: float,
) -> None:
    """Tip TRB for a selected query ID"""
    legacy_id = ctx.obj["LEGACY_ID"]

    click.echo(f"Tipping {amount_trb} TRB for legacy ID {legacy_id}.")

    endpoint = cfg.get_endpoint()

    _, oracle = get_tellor_contracts(
        private_key=cfg.main.private_key, endpoint=endpoint, chain_id=cfg.main.chain_id
    )

    chosen_feed = LEGACY_DATAFEEDS[legacy_id]
    tip = int(amount_trb * 1e18)

    tx_receipt, status = asyncio.run(
        tip_query(
            oracle=oracle,
            datafeed=chosen_feed,
            tip=tip,
        )
    )

    if status.ok and not status.error and tx_receipt:
        click.echo("Success!")
        tx_hash = tx_receipt["transactionHash"].hex()
        # Point to relevant explorer
        logger.info(f"View tip: \n{endpoint.explorer}/tx/{tx_hash}")
    else:
        logger.error(status)


if __name__ == "__main__":
    cli()
