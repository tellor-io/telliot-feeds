""" Telliot Feed Examples CLI

A simple interface for interacting with telliot example feed functionality.
"""
import asyncio
from typing import Any
from typing import Mapping

import click
from click.core import Context
from telliot_core.apps.core import TelliotCore
from telliot_feed_examples import flashbots

from telliot_feed_examples.feeds import LEGACY_DATAFEEDS
from telliot_feed_examples.flashbots import flashbot
from telliot_feed_examples.reporters.interval import FlashbotsReporter, IntervalReporter
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
    
    # Apply the FLASHBOTS_RELAY flag
    flashbots_relay = obj["FLASHBOTS_RELAY"]
    if flashbots_relay is not None:
        assert app.config
        if flashbots_relay == "mainnet":
            app.config.main.chain_id = 1
        if flashbots_relay == "testnet":
            app.config.main.chain_id = 5

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
    # goerli endpoint used in the test.

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
@click.option(
    "--flashbots",
    "-fb",
    "flashbots_relay",
    help="use flashbots relay to submit values",
    nargs=1,
    type=click.Choice(
        ["mainnet", "testnet"],
        case_sensitive=True,
    ),
    required=False
)
@click.pass_context
def cli(
    ctx: Context,
    private_key: str,
    chain_id: int,
    override_rpc_url: str,
    flashbots_relay: str,
) -> None:
    """Telliot command line interface"""
    ctx.ensure_object(dict)
    ctx.obj["PRIVATE_KEY"] = private_key
    ctx.obj["CHAIN_ID"] = chain_id
    ctx.obj["RPC_URL"] = override_rpc_url
    ctx.obj["FLASHBOTS_RELAY"] = flashbots_relay


# Report subcommand options
@cli.command()
@click.option(
    "--legacy-id",
    "-lid",
    "legacy_id",
    help="report to a legacy ID",
    required=True,
    nargs=1,
    type=click.Choice(["1", "2", "10", "41", "50", "59"]),
    default="1",  # ETH/USD spot price
)
@click.option(
    "--gas-limit",
    "-gl",
    "gas_limit",
    help="use custom gas limit",
    nargs=1,
    type=int,
    default=300000,
)
@click.option(
    "--priority-fee",
    "-pf",
    "priority_fee",
    help="use custom priority fee (gwei)",
    nargs=1,
    type=float,
    default=2.5,
)
@click.option(
    "--profit",
    "-p",
    "profit",
    help="lower threshold (inclusive) for expected percent profit",
    nargs=1,
    # User can omit profitability checks by specifying "YOLO"
    type=click.Choice([float, "YOLO"]),
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
    core = get_app(ctx.obj)  # Initialize telliot core app using CLI context

    flashbots_relay = ctx.obj["FLASHBOTS_RELAY"]
    if flashbots_relay is not None:
        click.echo(f"***** Using flashbots relay on {flashbots_relay} *****")

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

    common_reporter_kwargs = {
        "endpoint": core.endpoint,
        "private_key": core.get_default_staker().private_key,
        "master": core.tellorx.master,
        "oracle": core.tellorx.oracle,
        "datafeed": chosen_feed,
        "profit_threshold": profit_percent,
        "gas_price": gas_price,
        "max_gas_price": max_gas_price,
        "gas_price_speed": gas_price_speed,
        "gas_limit": gas_limit,
    }

    if flashbots_relay is not None:
        reporter = FlashbotsReporter(
            **common_reporter_kwargs,
            relay=flashbots_relay
        )
    else:
        reporter = IntervalReporter(**common_reporter_kwargs)

    if submit_once:
        _, _ = asyncio.run(reporter.report_once())
    else:
        _, _ = asyncio.run(reporter.report())


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
