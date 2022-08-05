import click
import eth_abi

from telliot_feeds.queries.abi_query import AbiQuery
from telliot_feeds.queries.json_query import JsonQuery
from telliot_feeds.queries.legacy_query import LegacyRequest
from telliot_feeds.queries.query import OracleQuery
from telliot_feeds.queries.query_catalog import query_catalog

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
    if query_data:
        decode_query_data(query_data)

    if submit_value_bytes:
        query = choose_query_type()
        decode_submit_value_bytes(query, submit_value_bytes)


def decode_query_data(query_data: str) -> None:
    """Decode query data."""
    if len(query_data) > 2 and query_data[:2] == "0x":
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
    for query in (AbiQuery, LegacyRequest, JsonQuery):
        q = query.get_query_from_data(query_data)  # type: ignore
        if q:
            break
    if q:
        click.echo(f"Query: {q}")
    else:
        click.echo("Unable to decode query data.")


def choose_query_type() -> OracleQuery:
    """Choose query type."""
    click.echo("Choose query type to decode submitted value:")
    queries = []
    names = set()
    for entry in query_catalog._entries.values():
        if entry.query_type not in names:
            names.add(entry.query_type)
            queries.append(entry.query)
            click.echo(f"[{len(queries)}] -- {entry.query_type}")

    choice = None
    while not choice:
        try:
            choice = int(input(f"Enter number from 1-{len(queries)}: "))
        except ValueError:
            click.echo("Invalid choice.")
            continue

        if choice < len(queries) + 1 < choice:
            choice = None
            click.echo("Invalid choice.")

    click.echo(f"Your choice: {type(queries[choice - 1]).__name__}")
    return queries[choice - 1]


def decode_submit_value_bytes(query: OracleQuery, submit_value_bytes: str) -> None:
    """Decode reported data."""
    if len(submit_value_bytes) > 2 and submit_value_bytes[:2] == "0x":
        submit_value_bytes = submit_value_bytes[2:]

    try:
        submit_value_bytes = bytes.fromhex(submit_value_bytes)  # type: ignore
    except ValueError:
        click.echo(
            "Invalid submit value bytes. Only hex strings accepted as input. Example Snapshot submit value bytes:\n"
            "0x0000000000000000000000000000000000000000000000000000000000000001"
        )
        return

    if isinstance(submit_value_bytes, bytes):
        try:
            click.echo(f"Decoded value: {query.value_type.decode(submit_value_bytes)}")
        except (eth_abi.exceptions.InsufficientDataBytes, eth_abi.exceptions.NonEmptyPaddingBytes):
            click.echo(f"Unable to decode value using query type: {query.__class__.__name__}")


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
