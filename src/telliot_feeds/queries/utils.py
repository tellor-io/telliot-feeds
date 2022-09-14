from typing import Any
from typing import Callable

from telliot_feeds.queries.query import OracleQuery
from telliot_feeds.queries.query_catalog import query_catalog


def choose_query_type(log: Callable[..., Any] = print) -> OracleQuery:
    """Choose query type."""
    log("Choose query type to decode submitted value:")
    queries = []
    names = set()
    for entry in query_catalog._entries.values():
        if entry.query_type not in names:
            names.add(entry.query_type)
            queries.append(entry.query)
            log(f"[{len(queries)}] -- {entry.query_type}")

    choice = None
    while not choice:
        try:
            choice = int(input(f"Enter number from 1-{len(queries)}: "))
        except ValueError:
            log("Invalid choice.")
            continue

        if choice < len(queries) + 1 < choice:
            choice = None
            log("Invalid choice.")

    log(f"Your choice: {type(queries[choice - 1]).__name__}")
    return queries[choice - 1]
