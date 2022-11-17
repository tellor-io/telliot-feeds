import json
from typing import Any
from typing import Callable
from typing import List
from typing import Optional
from typing import Union

import click
import requests
from chained_accounts import ChainedAccount
from eth_typing import ChecksumAddress
from telliot_core.contract.contract import Contract
from telliot_core.directory import ContractInfo
from telliot_core.model.endpoints import RPCEndpoint
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


def create_custom_contract(
    original_contract: Contract,
    custom_contract_addr: ChecksumAddress,
    endpoint: RPCEndpoint,
    account: ChainedAccount,
    custom_abi: Any = None,
) -> Contract:
    """Verify custom contract ABI is compatible with the original contract ABI. Return custom contract instance.

    Custom contract ABI must have the same functions as the original contract ABI.
    Custom contract must be deployed and verified, so that the ABI can be retrieved. Otherwise,
    the user will need to provide the ABI as a JSON file."""
    original_functions = original_contract.all_functions()

    if not custom_abi:
        # fetch ABI from block explorer
        custom_abi = ContractInfo(name=None, org=None, address={endpoint.chain_id: custom_contract_addr}).get_abi(
            chain_id=endpoint.chain_id
        )

    custom_contract = Contract(custom_contract_addr, custom_abi, endpoint, account)
    custom_functions = custom_contract.all_functions()

    err_msg = "Custom contract ABI must have the same functions as the original contract ABI."
    for func in original_functions:
        if func not in custom_functions:
            raise ValueError(err_msg)

    return custom_contract


def prompt_for_abi() -> Any:
    """Prompt user to provide custom contract ABI as a JSON file."""
    file_path = click.prompt(
        "Please provide the path to the custom contract ABI as a JSON file", type=click.Path(exists=True)
    )
    with open(file_path, "r") as f:
        abi = json.load(f)
    return abi
