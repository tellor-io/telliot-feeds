import json
import random
from datetime import datetime
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
from web3.types import FeeHistory
from web3.types import Wei

from telliot_feeds.constants import ATLETA_CHAINS
from telliot_feeds.constants import ETHEREUM_CHAINS
from telliot_feeds.constants import FILECOIN_CHAINS
from telliot_feeds.constants import FRXETH_CHAINS
from telliot_feeds.constants import GNOSIS_CHAINS
from telliot_feeds.constants import KYOTO_CHAINS
from telliot_feeds.constants import MANTLE_CHAINS
from telliot_feeds.constants import POLYGON_CHAINS
from telliot_feeds.constants import PULSECHAIN_CHAINS
from telliot_feeds.constants import SKALE_CHAINS
from telliot_feeds.constants import TARAXA_CHAINS
from telliot_feeds.constants import TELOS_CHAINS
from telliot_feeds.datafeed import DataFeed
from telliot_feeds.feeds import CATALOG_FEEDS
from telliot_feeds.feeds.atla_helper_feed import atla_helper_feed
from telliot_feeds.feeds.eth_usd_feed import eth_usd_median_feed
from telliot_feeds.feeds.fil_usd_feed import fil_usd_median_feed
from telliot_feeds.feeds.frxeth_usd_feed import frxeth_usd_median_feed
from telliot_feeds.feeds.matic_usd_feed import matic_usd_median_feed
from telliot_feeds.feeds.mnt_usd_feed import mnt_usd_median_feed
from telliot_feeds.feeds.pls_usd_feed import pls_usd_median_feed
from telliot_feeds.feeds.sfuel_helper_feed import sfuel_helper_feed
from telliot_feeds.feeds.tara_usd_feed import tara_usd_median_feed
from telliot_feeds.feeds.tlos_usd_feed import tlos_usd_median_feed
from telliot_feeds.feeds.xdai_usd_feed import xdai_usd_median_feed
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


def suggest_random_feed() -> DataFeed[Any]:
    """Suggest a random feed to report against."""
    return random.choice(list(CATALOG_FEEDS.values()))


async def is_online() -> bool:
    """checks internet connection by pinging Cloudflare DNS"""
    try:
        requests.get("http://1.1.1.1")
        return True
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
        logger.error(f"Unable to connect to internet: {repr(e)}")
        return False


def alert_placeholder(msg: str) -> None:
    """Dummy alert function"""
    pass


def has_native_token_funds(
    account: ChecksumAddress,
    web3: Web3,
    alert: Callable[[str], None] = alert_placeholder,
    min_balance: int = 10**18,
) -> bool:
    """Check if an account has native token funds."""
    try:
        balance = web3.eth.get_balance(account)
    except Exception as e:
        logger.warning(f"Error fetching native token balance for {account}: {e}")
        return False

    if balance < min_balance:
        str_bal = f"{balance / 10**18:.2f}"
        expected = f"{min_balance / 10**18:.2f}"
        msg = f"Insufficient native token funds for {account}. Balance: {str_bal} ETH. Expected: {expected} ETH."
        logger.warning(msg)
        alert(msg)
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

    Reports to user if custom contract ABI differs from original contract ABI.
    Confirms if user wants to continue with custom contract ABI."""
    original_functions = sorted(list(original_contract.contract.functions))

    if not custom_abi:
        # fetch ABI from block explorer
        try:
            custom_abi = ContractInfo(name=None, org=None, address={endpoint.chain_id: custom_contract_addr}).get_abi(
                chain_id=endpoint.chain_id
            )
        except Exception as e:
            raise click.ClickException(f"Error fetching custom contract ABI from block explorer: {e}")

    custom_contract = Contract(custom_contract_addr, custom_abi, endpoint, account)
    custom_contract.connect()
    custom_functions = sorted(list(custom_contract.contract.functions))

    missing_functions = [f for f in original_functions if f not in custom_functions]
    if missing_functions:
        warning_msg = f"WARNING: Custom contract ABI is missing {len(missing_functions)} functions:"
        click.echo(warning_msg)
        numbered_missing_functions = "\n".join([f"{i+1:03d}. {f}" for i, f in enumerate(missing_functions)])
        click.echo(numbered_missing_functions)
        click.confirm("Continue?", default=True, abort=True)

    return custom_contract


def prompt_for_abi() -> Any:
    """Prompt user to provide custom contract ABI as a JSON file."""
    if click.confirm(
        "Do you want to provide a custom contract ABI? If no, will attempt to fetch from block explorer.", default=False
    ):
        file_path = click.prompt(
            "Provide path to custom contract ABI JSON file (e.g. /Users/foo/custom_reporter_abi.json)",
            type=click.Path(exists=True),
        )
        with open(file_path, "r") as f:
            abi = json.load(f)
        return abi
    return None


def get_native_token_feed(chain_id: int) -> DataFeed[float]:
    """Return native token feed for a given chain ID."""
    if chain_id in ETHEREUM_CHAINS:
        return eth_usd_median_feed
    elif chain_id in POLYGON_CHAINS:
        return matic_usd_median_feed
    elif chain_id in GNOSIS_CHAINS:
        return xdai_usd_median_feed
    elif chain_id in FILECOIN_CHAINS:
        return fil_usd_median_feed
    elif chain_id in PULSECHAIN_CHAINS:
        return pls_usd_median_feed
    elif chain_id in MANTLE_CHAINS:
        return mnt_usd_median_feed
    elif chain_id in FRXETH_CHAINS:
        return frxeth_usd_median_feed
    elif chain_id in KYOTO_CHAINS:
        return eth_usd_median_feed
    elif chain_id in SKALE_CHAINS:
        return sfuel_helper_feed
    elif chain_id in TELOS_CHAINS:
        return tlos_usd_median_feed
    elif chain_id in ATLETA_CHAINS:
        return atla_helper_feed
    elif chain_id in TARAXA_CHAINS:
        return tara_usd_median_feed
    else:
        raise ValueError(f"Cannot fetch native token feed. Invalid chain ID: {chain_id}")


def tkn_symbol(chain_id: int) -> str:
    if chain_id in POLYGON_CHAINS:
        return "MATIC"
    elif chain_id in GNOSIS_CHAINS:
        return "XDAI"
    elif chain_id in ETHEREUM_CHAINS:
        return "ETH"
    elif chain_id in FILECOIN_CHAINS:
        return "FIL"
    elif chain_id in PULSECHAIN_CHAINS:
        return "PLS"
    elif chain_id in MANTLE_CHAINS:
        return "MNT"
    elif chain_id in KYOTO_CHAINS:
        return "KYOTO"
    elif chain_id in FRXETH_CHAINS:
        return "frxETH"
    elif chain_id in SKALE_CHAINS:
        return "sFUEL"
    elif chain_id in TELOS_CHAINS:
        return "TLOS"
    elif chain_id in ATLETA_CHAINS:
        return "ATLA"
    elif chain_id in TARAXA_CHAINS:
        return "TARA"
    else:
        return "Unknown native token"


def fee_history_priority_fee_estimate(fee_history: FeeHistory, priority_fee_max: Wei) -> Wei:
    """Estimate priority fee based on a percentile of the fee history.

    Adapted from web3.py fee_utils.py

    Args:
        fee_history: Fee history object returned by web3.eth.fee_history
        priority_fee_max: Maximum priority fee willing to pay

    Returns:
        Estimated priority fee in wei
    """
    priority_fee_min = Wei(1_000_000_000)  # 1 gwei
    # grab only non-zero fees and average against only that list
    non_empty_block_fees = [fee[0] for fee in fee_history["reward"] if fee[0] != 0]

    # prevent division by zero in the extremely unlikely case that all fees within the polled fee
    # history range for the specified percentile are 0
    divisor = len(non_empty_block_fees) if len(non_empty_block_fees) != 0 else 1

    priority_fee_average_for_percentile = Wei(round(sum(non_empty_block_fees) / divisor))

    if priority_fee_average_for_percentile > priority_fee_max:
        return priority_fee_max
    elif priority_fee_average_for_percentile < priority_fee_min:
        return priority_fee_min
    else:
        return priority_fee_average_for_percentile


def current_time() -> int:
    return round(datetime.now().timestamp())
