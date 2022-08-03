import click

from telliot_feeds.queries.abi_query import AbiQuery
from telliot_feeds.queries.legacy_query import LegacyRequest

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
    """Decode query data."""
    if query_data is not None:
        if query_data[:2] == "0x":
            query_data = query_data[2:]
        try:
            query_data = bytes.fromhex(query_data)  # type: ignore
        except ValueError:
            click.echo(
                "Invalid query data. Only hex strings accepted as input. Example Snapshot query data:\n"
                "0x00000000000000000000000000000000000000000000000000000000000000400"
                "0000000000000000000000000000000000000000000000000000000000000800000"
                "000000000000000000000000000000000000000000000000000000000008536e617"
                "073686f740000000000000000000000000000000000000000000000000000000000"
                "0000000000000000000000000000000000000000000000000000800000000000000"
                "0000000000000000000000000000000000000000000000000200000000000000000"
                "0000000000000000000000000000000000000000000000406363653937363061646"
                "5613930363137363934306165356664303562633030376363393235326235323438"
                "333230363538303036333534383463623563623537"
            )
        q = None
        for query in (AbiQuery, LegacyRequest):
            q = query.get_query_from_data(query_data)  # type: ignore
            if q:
                break
        if q:
            print(q)
        else:
            print("Unable to decode query data.")

    if submit_value_bytes is not None:
        click.echo(submit_value_bytes)


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
#             print(f"Unknown query tag: {query_tag}.")
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
#         print(f"Timestamp count: {count}")
#         bytes_value, status = await tellorx.oracle.getCurrentValue(queryId)
#         if bytes_value is not None:
#             value = q.value_type.decode(bytes_value)
#             print(f"Current value: {value}")
#         else:
#             print("Current value: None")
#         tlnv, status = await tellorx.oracle.getTimeOfLastNewValue()
#         print(f"Time of last new value (all queryIds): {tlnv}")
#         tips, status = await tellorx.oracle.getTipsById(queryId)
#         print(f"Tips (TRB): {tips}")
#         (tips2, reward), status = await tellorx.oracle.getCurrentReward(queryId)
#         print(f"Tips/reward (TRB): {tips2} / {reward}")
#         if count > 0:
#             print(f"{npoints} most recent on-chain datapoints:")
#             for k in range(count - npoints, count):
#                 ts, status = await tellorx.oracle.getReportTimestampByIndex(queryId, k)
#                 blocknum, status = await tellorx.oracle.getBlockNumberByTimestamp(queryId, ts)
#                 bytes_value, status = await tellorx.oracle.getValueByTimestamp(queryId, ts)
#                 value = q.value_type.decode(bytes_value)
#                 reporter, status = await tellorx.oracle.getReporterByTimestamp(queryId, ts)
#                 print(f" index: {k}, timestamp: {ts}, block: {blocknum}, value:{value}, reporter: {reporter} ")
#         else:
#             print("No on-chain datapoints found.")


# @query.command()
# @click.pass_context
# @async_run
# async def suggest(ctx: click.Context) -> None:
#     """Get the current suggested query for reporter synchronization."""
#     async with cli_core(ctx) as core:
#         tellorx = core.get_tellorx_contracts()
#         qtag = await tellor_suggested_report(tellorx.oracle)
#         assert isinstance(qtag, str)
#         print(f"Suggested query: {qtag}")
