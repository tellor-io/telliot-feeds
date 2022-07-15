from typing import Any
from typing import Optional
from typing import Tuple

from telliot_core.contract.contract import Contract
from telliot_core.utils.response import ResponseStatus
from web3.datastructures import AttributeDict

from telliot_feeds.datafeed import DataFeed
from telliot_feeds.utils.contract import write_with_retry
from telliot_feeds.utils.log import get_logger

logger = get_logger(__name__)


async def tip_query(
    oracle: Contract,
    datafeed: DataFeed[Any],
    tip: int,
    gas_price: str = "3",
    retries: int = 2,
) -> Tuple[Optional[AttributeDict[Any, Any]], ResponseStatus]:
    """Call the TellorX oracle contract's tipQuery function

    Tip TRB for the given datafeed's query ID to incentivise
    reporters to report relevant data."""
    tx_receipt, status = await write_with_retry(
        oracle,
        func_name="tipQuery",
        gas_limit=350000,
        legacy_gas_price=int(gas_price),
        extra_gas_price=20,
        retries=retries,
        _queryId=datafeed.query.query_id,
        _queryData=datafeed.query.query_data,
        _tip=tip,
    )

    return tx_receipt, status
