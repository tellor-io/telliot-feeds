from typing import Callable
from typing import List
from typing import Optional
from typing import Union

import requests
from telliot_core.contract.contract import Contract
from telliot_core.tellor.tellorflex.oracle import TellorFlexOracleContract
from telliot_core.tellor.tellorx.oracle import TellorxOracleContract

from telliot_feeds.queries.query_catalog import query_catalog
from telliot_feeds.utils.log import get_logger

logger = get_logger(__name__)

# List of currently active reporters
reporter_sync_schedule: List[str] = [qt for qt in query_catalog._entries.keys() if "spot" in qt]


async def tellor_suggested_report(
    oracle: Union[TellorxOracleContract, TellorFlexOracleContract],
) -> Optional[str]:
    """Returns the currently suggested query to report against.

    The suggested query changes each time a block contains a query response.
    The time of last report is used to randomly index into the
    `report_sync_schedule` to determine the suggested query.

    """
    try:
        timestamp, status = await oracle.getTimeOfLastNewValue()
    except AttributeError:
        timestamp, status = await oracle.get_time_of_last_new_value()
    except Exception as e:
        msg = f"Unable to fetch timestamp of last new value: {e}"
        logger.warning(msg)
        return None

    if status.ok:
        suggested_idx = timestamp.ts % len(reporter_sync_schedule)
        suggested_qtag = reporter_sync_schedule[suggested_idx]
        assert isinstance(suggested_qtag, str)
        return suggested_qtag

    else:
        return None


async def is_online() -> bool:
    """checks internet connection by pinging Cloudflare DNS"""
    try:
        requests.get("http://1.1.1.1")
        return True
    except requests.exceptions.ConnectionError:
        return False


def alert_placeholder(msg: str) -> None:
    """Dummy alert function"""
    pass


async def has_native_token_funds(
    account: str, token_contract: Contract, alert: Callable[str] = alert_placeholder, min_balance: int = 10**18
) -> bool:
    """Check if an account has native token funds."""
    balance, status = token_contract.read(
        func_name="balanceOf",
        _address=account,
    )
    if status.ok:
        if balance < min_balance:
            logger.warning(f"Account {account} has insufficient native token funds")
            alert(f"Account {account} has insufficient native token funds")
            return False

        return True

    logger.warning(f"Unable to fetch native token balance for {account}")
    alert(f"Unable to fetch native token balance for account {account}")
    return False
