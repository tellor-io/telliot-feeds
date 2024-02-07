import functools
import os
from typing import Any
from typing import Callable
from typing import cast
from typing import Dict
from typing import get_args
from typing import get_type_hints
from typing import Optional
from typing import Type
from typing import Union

import click
from chained_accounts import ChainedAccount
from chained_accounts import find_accounts
from dotenv import load_dotenv
from eth_typing import ChecksumAddress
from eth_utils import to_checksum_address
from hexbytes import HexBytes
from simple_term_menu import TerminalMenu
from telliot_core.apps.core import TelliotCore
from telliot_core.cli.utils import cli_core

from telliot_feeds.cli.constants import REWARDS_CHECK_MESSAGE
from telliot_feeds.cli.constants import STAKE_MESSAGE
from telliot_feeds.constants import DIVA_PROTOCOL_CHAINS
from telliot_feeds.datafeed import DataFeed
from telliot_feeds.feeds import DATAFEED_BUILDER_MAPPING
from telliot_feeds.queries.abi_query import AbiQuery
from telliot_feeds.queries.query_catalog import query_catalog
from telliot_feeds.reporters.gas import GasFees
from telliot_feeds.utils.cfg import check_endpoint
from telliot_feeds.utils.cfg import setup_config
from telliot_feeds.utils.reporter_utils import has_native_token_funds

load_dotenv()


def print_reporter_settings(
    signature_address: str,
    query_tag: str,
    gas_limit: int,
    base_fee: Optional[float],
    priority_fee: Optional[float],
    max_fee: Optional[float],
    expected_profit: str,
    chain_id: int,
    transaction_type: int,
    legacy_gas_price: Optional[int],
    reporting_diva_protocol: bool,
    stake_amount: float,
    min_native_token_balance: float,
) -> None:
    """Print user settings to console."""
    click.echo("")

    if signature_address != "":
        click.echo("⚡🤖⚡ Reporting through Flashbots relay ⚡🤖⚡")
        click.echo(f"Signature account: {signature_address}")

    if query_tag:
        click.echo(f"Reporting query tag: {query_tag}")
    elif reporting_diva_protocol:
        click.echo("Reporting & settling DIVA Protocol pools")
    else:
        click.echo("Reporting with synchronized queries")

    click.echo(f"Current chain ID: {chain_id}")

    if expected_profit == "YOLO":
        click.echo("🍜🍜🍜 Reporter not enforcing profit threshold! 🍜🍜🍜")
    else:
        click.echo(f"Expected percent profit: {expected_profit}%")

    click.echo(f"Transaction type: {transaction_type}")
    click.echo(f"Gas Limit: {gas_limit}")
    click.echo(f"Legacy gas price (gwei): {legacy_gas_price}")
    click.echo(f"Max fee (gwei): {max_fee}")
    click.echo(f"Priority fee (gwei): {priority_fee}")
    click.echo(f"Desired stake amount: {stake_amount}")
    click.echo(f"Minimum native token balance (e.g. ETH if on Ethereum mainnet): {min_native_token_balance}")
    click.echo("\n")


def parse_profit_input(ctx: click.Context, param: Any, value: str) -> Optional[Union[str, float]]:
    """Parses user input expected profit and ensures
    the input is either a float or the string 'YOLO'."""
    if value == "YOLO":
        return value
    else:
        try:
            return float(value)
        except ValueError:
            raise click.BadParameter("Not a valid profit input. Enter float or the string, 'YOLO'")


def reporter_cli_core(ctx: click.Context) -> TelliotCore:
    """Get telliot core configured in reporter CLI context"""
    # Delegate to main cli core getter
    # (handles ACCOUNT_NAME, CHAIN_ID, and TEST_CONFIG)
    core = cli_core(ctx)

    # Ensure chain id compatible with flashbots relay
    if ctx.obj.get("SIGNATURE_ACCOUNT_NAME", None) is not None:
        # Only supports mainnet
        assert core.config.main.chain_id in (1, 5, 11155111)

    if ctx.obj["TEST_CONFIG"]:
        try:
            from brownie import chain
        except ModuleNotFoundError:
            print("pip install -r requirements-dev.txt in venv to use test config")

        # core.config.main.chain_id = 1337
        core.config.main.url = "http://127.0.0.1:8545"

        chain.mine(10)

        accounts = find_accounts(chain_id=1337)
        if not accounts:
            # Create a test account using PRIVATE_KEY defined on github.
            key = os.getenv("PRIVATE_KEY", None)
            if key:
                ChainedAccount.add(
                    "git-tellorflex-test-key",
                    chains=1337,
                    key=key,
                    password="",
                )
            else:
                raise Exception("Need an account for chain_id 1337")

    assert core.config

    return core


def valid_diva_chain(chain_id: int) -> bool:
    """Ensure given chain ID supports reporting Diva Protocol data."""
    if chain_id not in DIVA_PROTOCOL_CHAINS:
        print(f"Current chain id ({chain_id}) not supported for reporting DIVA Protocol data.")
        return False
    return True


def convert_input(target_type: Callable[[Union[str, int, float]], Any], input_str: str) -> Any:
    """Convert an input string from cli to whatever type is needed for the QueryParameter"""
    if target_type == bytes:
        if input_str.startswith("0x"):
            return bytes.fromhex(input_str[2:])
    if target_type == int:
        return int(input_str)
    elif target_type == float:
        return float(input_str)
    elif target_type == str:
        return input_str
    else:
        return target_type(input_str)


def build_feed_from_input() -> Optional[DataFeed[Any]]:
    """
    Build a DataFeed from CLI input
    Called when the --build-feed flag is used on the telliot-feeds CLI

    This function takes input from the user for the QueryType
    and its matching QueryParameters, the builds a DataFeed
    object if the QueryType is supported and the QueryParameters
    can be casted to their appropriate data types from an input string.

    Returns: DataFeed[Any]

    """
    try:
        num_feeds = len(DATAFEED_BUILDER_MAPPING)
        # list choices
        click.echo("Choose query type:")
        for i, q_type in enumerate(sorted(DATAFEED_BUILDER_MAPPING.keys())):
            choice_num = f"{i + 1}".zfill(len(str(num_feeds)))
            click.echo(f"{choice_num} -- {q_type}")

        # get user choice
        choice = None
        query_type = None
        while not choice or not query_type:
            try:
                choice = int(input(f"Enter number from 1-{num_feeds}: "))
                query_type = sorted(DATAFEED_BUILDER_MAPPING.keys())[choice - 1]
            except (ValueError, IndexError):
                choice = None
                query_type = None
                click.echo("Invalid choice.")
                continue

        click.echo("Your choice: " + query_type)
        feed: DataFeed[Any] = DATAFEED_BUILDER_MAPPING[query_type]
    except KeyError:
        click.echo(f"No corresponding datafeed found for QueryType: {query_type}\n")
        return None
    for query_param in feed.query.__dict__.keys():
        # accessing the datatype
        type_hints = get_type_hints(feed.query)
        # get param type if type isn't optional
        try:
            param_dtype = get_args(type_hints[query_param])[0]  # parse out Optional type
        except IndexError:
            param_dtype = type_hints[query_param]

        val = input(f"Enter value for QueryParameter {query_param}: ")

        if val is not None:
            try:
                # cast input from string to datatype of query parameter
                val = convert_input(param_dtype, val)
                setattr(feed.query, query_param, val)
                setattr(feed.source, query_param, val)
            except ValueError:
                click.echo(f"Value {val} for QueryParameter {query_param} does not match type {param_dtype}")
                return None

        else:
            click.echo(f"Must set QueryParameter {query_param} of QueryType {query_type}")
            return None

    return feed


def build_query(log: Optional[Callable[[str], None]] = click.echo) -> Any:
    """Build a query from CLI input"""
    title = "Select a query type:"
    queries = [q for q in AbiQuery.__subclasses__() if q.__name__ not in ("LegacyRequest")]
    options = [q.__name__ for q in queries]
    # Sort options and queries by alphabetical order
    options, queries = [zip(*sorted(zip(options, queries)))]

    menu = TerminalMenu(options, title=title)
    selected_index = menu.show()
    q = queries[selected_index]

    if not q:
        log("No query selected")
        return None

    # Get query parameters
    query_params = {}
    for name, field in q.__dataclass_fields__.items():
        try:
            val = click.prompt(name, type=field.type)
        except AttributeError:
            val = click.prompt(name, type=get_args(field.type)[0])

        query_params[name] = val

    try:
        query = q(**query_params)
        log("Query built successfully")
    except Exception as e:
        log(f"Error building query: {e}")
        return None

    log(query)
    log(f"Query ID: 0x{query.query_id.hex()}")
    log(f"Query data: 0x{query.query_data.hex()}")

    return query


def validate_address(ctx: click.Context, param: Any, value: str) -> Optional[ChecksumAddress]:
    """Ensure input is a valid checksum address"""
    # Sets default to None if no value is provided
    if not value:
        return None

    try:
        return to_checksum_address(value)
    except Exception as e:
        raise click.BadParameter(f"Address must be a valid hex string. Error: {e}")


def valid_transaction_type(ctx: click.Context, param: Any, value: str) -> int:
    """Ensure input is a valid transaction type"""
    supported = (0, 2)
    try:
        if int(value) in supported:
            return int(value)
        raise click.BadParameter(f"Transaction type given ({value}) is not supported ({supported}).")
    except ValueError:
        raise click.BadParameter("Transaction type must be an integer.")


def get_accounts_from_name(name: Optional[str]) -> list[ChainedAccount]:
    """Get account from name or return any account if no name is given."""
    accounts: list[ChainedAccount] = find_accounts(name=name) if name else find_accounts()
    if not accounts:
        click.echo(
            f'No account found named: "{name}".\nAdd one with the account subcommand.'
            "\nFor more info run: `telliot account add --help`"
        )
    return accounts


def common_reporter_options(f: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator for common options between reporter commands"""

    @click.option(
        "--query-tag",
        "-qt",
        "query_tag",
        help="select datafeed using query tag",
        required=False,
        nargs=1,
        type=click.Choice([q.tag for q in query_catalog.find()]),
    )
    @click.option(
        "-wp", "--wait-period", help="wait period between feed suggestion calls", nargs=1, type=int, default=7
    )
    @click.option("--submit-once/--submit-continuous", default=False)
    @click.option("--stake", "-s", "stake", help=STAKE_MESSAGE, nargs=1, type=float, default=10.0)
    @click.option(
        "--check-rewards/--no-check-rewards",
        "-cr/-ncr",
        "check_rewards",
        default=True,
        help=REWARDS_CHECK_MESSAGE,
    )
    @click.option(
        "--profit",
        "-p",
        "expected_profit",
        help="lower threshold (inclusive) for expected percent profit",
        nargs=1,
        # User can omit profitability checks by specifying "YOLO"
        type=click.UNPROCESSED,
        required=False,
        callback=parse_profit_input,
        default="100.0",
    )
    @click.option(
        "--skip-manual-feeds",
        help="skip feeds that require manual value input when listening to tips",
        nargs=1,
        type=bool,
        default=True,
    )
    @functools.wraps(f)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        return f(*args, **kwargs)

    return wrapper


def common_options(f: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator for common options between commands"""

    @click.option(
        "--account",
        "-a",
        "account_str",
        help="Name of account used for reporting, staking, etc. More info: run `telliot account --help`",
        required=True,
        nargs=1,
        type=str,
    )
    @click.option(
        "--unsafe/--safe",
        "-u/-sf",
        "unsafe",
        help="Disables config confirmation prompts",
        required=False,
        default=True,
    )
    @click.option("--gas-limit", "-gl", "gas_limit", help="use custom gas limit", nargs=1, type=int)
    @click.option(
        "--max-fee",
        "-mf",
        "max_fee_per_gas",
        help="use custom maxFeePerGas (gwei)",
        nargs=1,
        type=float,
        required=False,
    )
    @click.option(
        "--priority-fee",
        "-pf",
        "priority_fee_per_gas",
        help="use custom maxPriorityFeePerGas (gwei)",
        nargs=1,
        type=float,
        required=False,
    )
    @click.option(
        "--base-fee",
        "-bf",
        "base_fee_per_gas",
        help="use custom baseFeePerGas (gwei)",
        nargs=1,
        type=float,
        required=False,
    )
    @click.option(
        "--gas-price",
        "-gp",
        "legacy_gas_price",
        help="use custom legacy gasPrice (gwei)",
        nargs=1,
        type=int,
        required=False,
    )
    @click.option("-pwd", "--password", type=str)
    @click.option(
        "--tx-type",
        "-tx",
        "tx_type",
        help="choose transaction type (0 for legacy txs, 2 for EIP-1559)",
        type=click.UNPROCESSED,
        required=False,
        callback=valid_transaction_type,
        default=2,
    )
    @click.option(
        "--min-native-token-balance",
        "-mnb",
        "min_native_token_balance",
        help="Minimum native token balance required to report. Denominated in ether.",
        nargs=1,
        type=float,
        default=0.25,
    )
    @click.option(
        "--gas-multiplier",
        "-gm",
        "gas_multiplier",
        help="increase gas price for legacy transaction by this percentage (default 1%) ie 5 = 5%",
        nargs=1,
        type=int,
        default=1,  # 1% above the gas price by web3
    )
    @click.option(
        "--max-priority-fee-range",
        "-mpfr",
        "max_priority_fee_range",
        help="the maximum range of priority fees to use in gwei (default 3 gwei)",
        nargs=1,
        type=int,
        default=3,  # 3 gwei
    )
    @functools.wraps(f)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        return f(*args, **kwargs)

    return wrapper


async def call_oracle(
    *,
    ctx: click.Context,
    func: str,
    user_inputs: Dict[str, Any],
    **params: Any,
) -> None:
    # Initialize telliot core app using CLI context
    async with reporter_cli_core(ctx) as core:

        core._config, account = setup_config(core.config, account_name=ctx.obj.get("ACCOUNT_NAME"))

        endpoint = check_endpoint(core._config)

        if not endpoint or not account:
            click.echo("Accounts and/or endpoint unset.")
            click.echo(f"Account: {account}")
            click.echo(f"Endpoint: {core._config.get_endpoint()}")
            return

        # Make sure current account is unlocked
        if not account.is_unlocked:
            account.unlock(user_inputs.pop("password"))

        contracts = core.get_tellor360_contracts()
        # set private key for oracle interaction calls
        contracts.oracle._private_key = account.local_account.key
        min_native_token_balance = user_inputs.pop("min_native_token_balance")
        if has_native_token_funds(
            to_checksum_address(account.address),
            core.endpoint.web3,
            min_balance=int(min_native_token_balance * 10**18),
        ):
            gas = GasFees(endpoint=core.endpoint, account=account, **user_inputs)
            gas.update_gas_fees()
            gas_info = gas.get_gas_info_core()

            try:
                _ = await contracts.oracle.write(func, **params, **gas_info)
            except ValueError as e:
                if "no gas strategy selected" in str(e):
                    click.echo("Can't set gas fees automatically. Please specify gas fees manually.")


class CustomHexBytes(HexBytes):
    """Wrapper around HexBytes that doesn't accept int or bool"""

    def __new__(cls: Type[bytes], val: Union[bytearray, bytes, str]) -> "CustomHexBytes":
        if isinstance(val, (int, bool)):
            raise ValueError("Invalid value")
        return cast(CustomHexBytes, super().__new__(cls, val))
