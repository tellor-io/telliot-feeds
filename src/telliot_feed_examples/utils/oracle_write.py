from typing import Any
from typing import Optional
from typing import Tuple

from telliot_core.contract.contract import Contract
from telliot_core.datafeed import DataFeed
from telliot_core.utils.response import ResponseStatus
from web3.datastructures import AttributeDict


async def tip_query(
    oracle: Contract,
    datafeed: DataFeed,
    tip: int,
    gas_price: str = "3",
    retries: int = 2,
) -> Tuple[Optional[AttributeDict[Any, Any]], ResponseStatus]:
    """Call the TellorX oracle contract's tipQuery function

    Tip TRB for the given datafeed's query ID to incentivise
    reporters to report relevant data."""
    tx_receit, status = await oracle.write_with_retry(
        func_name="tipQuery",
        gas_price=gas_price,
        extra_gas_price=20,
        retries=retries,
        _queryId=datafeed.query.query_id,
        _queryData=datafeed.query.query_data,
        _tip=tip,
    )

    return tx_receit, status
