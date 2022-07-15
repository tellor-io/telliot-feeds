from typing import List
from typing import Optional
from typing import Union

from telliot_core.tellor.tellorflex.oracle import TellorFlexOracleContract
from telliot_core.tellor.tellorx.oracle import TellorxOracleContract

from telliot_feeds.queries.query_catalog import query_catalog

# List of currently active reporters
reporter_sync_schedule: List[str] = [qt for qt in query_catalog._entries.keys() if "legacy" in qt or "spot" in qt]
reporter_sync_schedule.remove("uspce-legacy")
reporter_sync_schedule.remove("ampl-legacy")
# print(reporter_sync_schedule)


async def tellor_suggested_report(
    oracle: Union[TellorxOracleContract, TellorFlexOracleContract],
) -> Optional[str]:
    """Returns the currently suggested query to report against.

    The suggested query changes each time a block contains a query response.
    The time of last report is used to randomly index into the
    `report_sync_schedule` to determine the suggested query.

    """
    chain = oracle.node.chain_id

    if chain in (1, 4):
        assert isinstance(oracle, TellorxOracleContract)
        timestamp, status = await oracle.getTimeOfLastNewValue()
    elif chain in (137, 80001):
        assert isinstance(oracle, TellorFlexOracleContract)
        timestamp, status = await oracle.get_time_of_last_new_value()
    else:
        return None

    if status.ok:
        suggested_idx = timestamp.ts % len(reporter_sync_schedule)
        suggested_qtag = reporter_sync_schedule[suggested_idx]
        assert isinstance(suggested_qtag, str)
        return suggested_qtag

    else:
        return None
