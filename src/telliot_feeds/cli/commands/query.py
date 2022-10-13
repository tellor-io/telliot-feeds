import click

from telliot_feeds.cli.utils import build_query
from telliot_feeds.queries.utils import choose_query_type
from telliot_feeds.utils.decode import decode_query_data
from telliot_feeds.utils.decode import decode_submit_value_bytes

# from telliot_core.cli.utils import async_run
# from telliot_core.cli.utils import cli_core

# from telliot_feeds.queries.query_catalog import query_catalog
# from telliot_feeds.utils.reporter_utils import tellor_suggested_report


@click.group()
def query() -> None:
    """Decode query data, query responses, & build custom queries."""
    pass


@query.command()
@click.option("--query-data", "-qd")
@click.option("--submit-value-bytes", "-svb")
def decode(query_data: str, submit_value_bytes: str) -> None:
    """Decode query data or reported value."""
    query = None
    if query_data:
        status, q = decode_query_data(query_data=query_data, log=click.echo)
        if status.ok:
            query = q

    if submit_value_bytes:
        if not query:
            query = choose_query_type()
        _, _ = decode_submit_value_bytes(query, submit_value_bytes, log=click.echo)


@query.command()
def new() -> None:
    """Build a new custom query."""
    _ = build_query()


# @query.command()
# @click.pass_context
# @click.argument("query_tag", type=str)
# @click.option(
#     "--npoints",
#     type=int,
#     default=1,
#     help="Number of datapoints to retrieve from block chain (most recent)",
# )
# @async_run
# async def status(ctx: click.Context, query_tag: str, npoints: int) -> None:
#     """Show query information
#     QUERY_TAG: Use `telliot catalog list` for list of valid query tags
#     """
#     async with cli_core(ctx) as core:
#         chain_id = core.config.main.chain_id
#         entries = query_catalog.find(tag=query_tag)
#         if len(entries) == 0:
#             click.echo(f"Unknown query tag: {query_tag}.")
#             return
#         else:
#             catalog_entry = entries[0]
#         # Get the query object from the catalog entry
#         q = catalog_entry.query
#         queryId = f"0x{q.query_id.hex()}"
#         if chain_id in [1, 4]:
#             tellorx = core.get_tellorx_contracts()
#         else:
#             click.echo(f"Query status not yet supported on Chain ID {chain_id}.")
#             return
#         count, status = await tellorx.oracle.getTimestampCountById(queryId)
#         click.echo(f"Timestamp count: {count}")
#         bytes_value, status = await tellorx.oracle.getCurrentValue(queryId)
#         if bytes_value is not None:
#             value = q.value_type.decode(bytes_value)
#             click.echo(f"Current value: {value}")
#         else:
#             click.echo("Current value: None")
#         tlnv, status = await tellorx.oracle.getTimeOfLastNewValue()
#         click.echo(f"Time of last new value (all queryIds): {tlnv}")
#         tips, status = await tellorx.oracle.getTipsById(queryId)
#         click.echo(f"Tips (TRB): {tips}")
#         (tips2, reward), status = await tellorx.oracle.getCurrentReward(queryId)
#         click.echo(f"Tips/reward (TRB): {tips2} / {reward}")
#         if count > 0:
#             click.echo(f"{npoints} most recent on-chain datapoints:")
#             for k in range(count - npoints, count):
#                 ts, status = await tellorx.oracle.getReportTimestampByIndex(queryId, k)
#                 blocknum, status = await tellorx.oracle.getBlockNumberByTimestamp(queryId, ts)
#                 bytes_value, status = await tellorx.oracle.getValueByTimestamp(queryId, ts)
#                 value = q.value_type.decode(bytes_value)
#                 reporter, status = await tellorx.oracle.getReporterByTimestamp(queryId, ts)
#                 click.echo(f" index: {k}, timestamp: {ts}, block: {blocknum}, value:{value}, reporter: {reporter} ")
#         else:
#             click.echo("No on-chain datapoints found.")


# @query.command()
# @click.pass_context
# @async_run
# async def suggest(ctx: click.Context) -> None:
#     """Get the current suggested query for reporter synchronization."""
#     async with cli_core(ctx) as core:
#         tellorx = core.get_tellorx_contracts()
#         qtag = await tellor_suggested_report(tellorx.oracle)
#         assert isinstance(qtag, str)
#         click.echo(f"Suggested query: {qtag}")
