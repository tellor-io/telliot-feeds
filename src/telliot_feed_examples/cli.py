""" Telliot Feed Examples CLI

A simple interface for interacting with telliot example feed functionality.
"""
import asyncio
from typing import Any
from typing import Mapping

import click
from click.core import Context
from telliot_core.apps.core import TelliotCore

from telliot_feed_examples.feeds import LEGACY_DATAFEEDS
from telliot_feed_examples.reporters.interval import IntervalReporter
from telliot_feed_examples.utils.log import get_logger
from telliot_feed_examples.utils.oracle_write import tip_query

logger = get_logger(__name__)


def get_app(obj: Mapping[str, Any]) -> TelliotCore:
    """Get an app configured using CLI context"""

    app = TelliotCore.get() or TelliotCore()

    # Apply the CHAIN_ID flag
    chain_id = obj["CHAIN_ID"]
    if chain_id is not None:
        assert app.config
        app.config.main.chain_id = chain_id

    # Apply the RPC_URL FLAG
    # Again, this is kinda hacky, because the RPC URL flag does not specify
    # an entire endpoint including exporer, etc.
    # But we'll just get the current endpoint and overwrite the URL.
    # We should prob delete this flag.
    if obj["RPC_URL"] is not None:
        app.endpoint.url = obj["RPC_URL"]

    # Apply the PRIVATE_KEY flag
    # Note: Ideally, the PRIVATE KEY flag is deprecated and replaced with the "staker tag"
    # provided by the user in stakers.yaml
    # This temporary hack will override the private key and address of the default staker.
    if obj["PRIVATE_KEY"] is not None:
        default_staker = app.get_default_staker()
        default_staker.private_key = obj["PRIVATE_KEY"]
        default_staker.address = "0x0"

    # Finally, tell the app to connect
    _ = app.connect()

    # Now overriding RPC URL is getting *really* ugly...
    # Forcibly update the chain_id because it might have changed above
    app.config.main.chain_id = app.endpoint.web3.eth.chain_id
    # This can throw everything out of sync.  We don't know if there is a staker
    # for the particular chain ID In fact, there is not normally one for the
    # goerly endpoint used in the test.

    assert app.config
    assert app.tellorx

    return app


# Main CLI options
@click.group()
@click.option(
    "--private-key",  # flag option 1
    "-pk",  # flag option 2
    "private_key",  # variable name of user input
    help="override the config's private key",
    required=False,
    nargs=1,
    type=str,
)
@click.option(
    "--chain-id",
    "-cid",
    "chain_id",
    help="override the config's chain ID",
    required=False,
    nargs=1,
    type=int,
)
@click.option(
    "--rpc-url",
    "-rpc",
    "override_rpc_url",
    help="override the config RPC url",
    nargs=1,
    type=str,
    required=False,
)
@click.pass_context
def cli(
    ctx: Context,
    private_key: str,
    chain_id: int,
    override_rpc_url: str,
) -> None:
    """Telliot command line interface"""
    ctx.ensure_object(dict)
    ctx.obj["PRIVATE_KEY"] = private_key
    ctx.obj["CHAIN_ID"] = chain_id
    ctx.obj["RPC_URL"] = override_rpc_url


# Report subcommand options
@cli.command()
@click.option(
    "--legacy-id",
    "-lid",
    "legacy_id",
    help="report to a legacy ID",
    required=True,
    nargs=1,
    type=str,
    default=1,  # ETH/USD spot price
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
    default=100.0,
)
@click.option("--submit-once/--submit-continuous", default=False)
@click.pass_context
def report(
    ctx: Context,
    legacy_id: str,
    gas_limit: int,
    gas_price: int,
    max_gas_price: int,
    gas_price_speed: str,
    submit_once: bool,
    profit_percent: float,
) -> None:
    """Report values to Tellor oracle"""
    # Ensure valid legacy id
    if legacy_id not in LEGACY_DATAFEEDS:
        click.echo(
            f"Invalid legacy ID. Valid choices: {', '.join(list(LEGACY_DATAFEEDS))}"
        )
        return

    core = get_app(ctx.obj)  # Initialize telliot core app using CLI context

    # Print user settings to console
    click.echo(f"Reporting legacy ID: {legacy_id}")
    click.echo(f"Current chain ID: {core.config.main.chain_id}")

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

    chosen_feed = LEGACY_DATAFEEDS[legacy_id]

    legacy_reporter = IntervalReporter(
        endpoint=core.endpoint,
        private_key=core.get_default_staker().private_key,
        master=core.tellorx.master,
        oracle=core.tellorx.oracle,
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
    "--legacy-id",
    "-lid",
    "legacy_id",
    help="report to a legacy ID",
    required=True,
    nargs=1,
    type=str,
    default=1,  # ETH/USD spot price
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
def tip(
    ctx: Context,
    legacy_id: str,
    amount_trb: float,
) -> None:
    """Tip TRB for a selected query ID"""

    core = get_app(ctx.obj)  # Initialize telliot core app using CLI context

    # Ensure valid legacy id
    if legacy_id not in LEGACY_DATAFEEDS:
        click.echo(
            f"Invalid legacy ID. Valid choices: {', '.join(list(LEGACY_DATAFEEDS))}"
        )
        return

    click.echo(f"Tipping {amount_trb} TRB for legacy ID {legacy_id}.")

    chosen_feed = LEGACY_DATAFEEDS[legacy_id]
    tip = int(amount_trb * 1e18)

    tx_receipt, status = asyncio.run(
        tip_query(
            oracle=core.tellorx.oracle,
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


if __name__ == "__main__":
    cli()
