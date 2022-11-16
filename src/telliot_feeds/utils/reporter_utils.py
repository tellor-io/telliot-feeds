from typing import Callable
from typing import List
from typing import Optional
from typing import Union

import requests
from eth_typing import ChecksumAddress
from telliot_core.tellor.tellorflex.oracle import TellorFlexOracleContract
from telliot_core.tellor.tellorx.oracle import TellorxOracleContract
from web3 import Web3

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


def has_native_token_funds(
    account: ChecksumAddress,
    web3: Web3,
    alert: Callable[[str], None] = alert_placeholder,
    min_balance: int = 1 * 10**18,
) -> bool:
    """Check if an account has native token funds."""
    try:
        balance = web3.eth.get_balance(account)
    except Exception as e:
        logger.warning(f"Error fetching native token balance for {account}: {e}")
        return False

    if balance < min_balance:
        logger.warning(f"Account {account} has insufficient native token funds")
        alert(f"Account {account} has insufficient native token funds")
        return False

    return True
