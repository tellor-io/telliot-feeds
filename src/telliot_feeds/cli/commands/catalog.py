from typing import Optional

import click

from telliot_feeds.queries.catalog import CatalogEntry
from telliot_feeds.queries.query_catalog import query_catalog


def dump_catalog_entry(entry: CatalogEntry, detail: bool = False) -> None:
    if not detail:
        print(f"{entry.tag:15} {entry.query_id} {entry.descriptor}")
    else:
        print(f"{entry.title}")
        print(f"  Tag: {entry.tag}")
        print(f"  Active: {entry.active}")
        print(f"  Type: {entry.query_type}")
        print(f"  Descriptor: {entry.descriptor}")
        print(f"  Query ID: {entry.query_id}")
        print(f"  Query data: 0x{entry.query.query_data.hex()}")


@click.group()
def catalog() -> None:
    """Browse and search the query catalog."""
    pass


@catalog.command()
@click.pass_context
@click.option("--tag", type=str, help="Filter for query tag")
@click.option("--id", type=str, help="Filter for query ID")
@click.option("--type", type=str, help="Filter for Query Type (e.g. SpotPrice)")
def search(
    ctx: click.Context,
    tag: Optional[str] = None,
    id: Optional[str] = None,
    # #type: Optional[str] = None,
) -> None:
    """Search the catalog for queries matching selected filters."""
    if tag is None and id is None and type is None:
        print(ctx.command.get_help(ctx))
        return
    entries = query_catalog.find(tag=tag, query_id=id, query_type=type)  # type: ignore
    for entry in entries:
        dump_catalog_entry(entry)


@catalog.command()
@click.option("-d", "--detail", is_flag=True, help="Print detailed information for each query")
def list(detail: bool) -> None:
    """List all queries in the catalog (use --detail for verbose output)."""
    entries = query_catalog.find()
    print("Query Tag       Query ID                                                           Query Descriptor")
    for entry in entries:
        dump_catalog_entry(entry, detail)
