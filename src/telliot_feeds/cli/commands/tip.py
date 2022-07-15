import asyncio

import click
from click.core import Context
from telliot_core.cli.utils import async_run

from telliot_feeds.cli.utils import reporter_cli_core
from telliot_feeds.datafeed import DataFeed
from telliot_feeds.feeds import CATALOG_FEEDS
from telliot_feeds.queries.query_catalog import query_catalog
from telliot_feeds.utils.log import get_logger
from telliot_feeds.utils.oracle_write import tip_query


logger = get_logger(__name__)


@click.group()
def tipper() -> None:
    """Tip query IDs to incentivise reporting."""
    pass


@tipper.command()
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
        if not isinstance(chosen_feed, DataFeed):
            click.echo(f"No corresponding datafeed found for given query tag: {query_tag}\n")
            return
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
