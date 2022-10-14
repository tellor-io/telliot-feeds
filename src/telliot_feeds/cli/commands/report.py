import getpass
from typing import Any
from typing import Optional
from typing import Union

import click
from chained_accounts import find_accounts
from click.core import Context
from eth_utils import to_checksum_address
from telliot_core.cli.utils import async_run
from telliot_core.contract.contract import Contract
from telliot_core.directory import ContractInfo

from telliot_feeds.cli.utils import build_feed_from_input
from telliot_feeds.cli.utils import reporter_cli_core
from telliot_feeds.cli.utils import valid_diva_chain
from telliot_feeds.cli.utils import validate_address
from telliot_feeds.datafeed import DataFeed
from telliot_feeds.feeds import CATALOG_FEEDS
from telliot_feeds.feeds.tellor_rng_feed import assemble_rng_datafeed
from telliot_feeds.integrations.diva_protocol import DIVA_DIAMOND_ADDRESS
from telliot_feeds.integrations.diva_protocol import DIVA_TELLOR_MIDDLEWARE_ADDRESS
from telliot_feeds.integrations.diva_protocol.report import DIVAProtocolReporter
from telliot_feeds.queries.query_catalog import query_catalog
from telliot_feeds.reporters.custom_flex_reporter import CustomFlexReporter
from telliot_feeds.reporters.custom_reporter import CustomXReporter
from telliot_feeds.reporters.flashbot import FlashbotsReporter
from telliot_feeds.reporters.interval import IntervalReporter
from telliot_feeds.reporters.rng_interval import RNGReporter
from telliot_feeds.reporters.tellor_360 import Tellor360Reporter
from telliot_feeds.reporters.tellorflex import TellorFlexReporter
from telliot_feeds.utils.cfg import check_endpoint
from telliot_feeds.utils.cfg import setup_config
from telliot_feeds.utils.log import get_logger


logger = get_logger(__name__)

TELLOR_X_CHAINS = (1, 4, 5)


def get_stake_amount() -> float:
    """Retrieve desired stake amount from user

    Each stake is 10 TRB on TellorFlex Polygon. If an address
    is not staked for any reason, the TellorFlexReporter will attempt
    to stake. Number of stakes determines the reporter lock:

    reporter_lock = 12hrs / N * stakes

    Retrieves desidred stake amount from user input."""

    warn = (
        "\n\U00002757Telliot will automatically stake more TRB "
        "if your stake is below or falls below the stake amount required to report.\n"
        "If you would like to stake more than required enter the TOTAL stake amount you wish to be staked.\n"
    )
    click.echo(warn)
    msg = "Enter amount TRB to stake if unstaked"
    stake = click.prompt(msg, type=float, default=10.0, show_default=True)
    assert isinstance(stake, float)
    assert stake >= 10.0

    return stake


def parse_profit_input(expected_profit: str) -> Optional[Union[str, float]]:
    """Parses user input expected profit and ensures
    the input is either a float or the string 'YOLO'."""
    if expected_profit == "YOLO":
        return expected_profit
    else:
        try:
            return float(expected_profit)
        except ValueError:
            click.echo("Not a valid profit input. Enter float or the string, 'YOLO'")
            return None


def print_reporter_settings(
    signature_address: str,
    query_tag: str,
    gas_limit: int,
    priority_fee: Optional[int],
    expected_profit: str,
    chain_id: int,
    max_fee: Optional[int],
    transaction_type: int,
    legacy_gas_price: Optional[int],
    gas_price_speed: str,
    reporting_diva_protocol: bool,
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
    click.echo(f"Gas price speed: {gas_price_speed}\n")


@click.group()
def reporter() -> None:
    """Report data on-chain."""
    pass


@reporter.command()
@click.option(
    "--build-feed",
    "-b",
    "build_feed",
    help="build a datafeed from a query type and query parameters",
    is_flag=True,
)
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
    "--gas-limit",
    "-gl",
    "gas_limit",
    help="use custom gas limit",
    nargs=1,
    type=int,
    default=350000,
)
@click.option(
    "--max-fee",
    "-mf",
    "max_fee",
    help="use custom maxFeePerGas (gwei)",
    nargs=1,
    type=int,
    required=False,
)
@click.option(
    "--priority-fee",
    "-pf",
    "priority_fee",
    help="use custom maxPriorityFeePerGas (gwei)",
    nargs=1,
    type=int,
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
@click.option(
    "--profit",
    "-p",
    "expected_profit",
    help="lower threshold (inclusive) for expected percent profit",
    nargs=1,
    # User can omit profitability checks by specifying "YOLO"
    type=str,
    default="100.0",
)
@click.option(
    "--tx-type",
    "-tx",
    "tx_type",
    help="choose transaction type (0 for legacy txs, 2 for EIP-1559)",
    type=int,
    default=0,
)
@click.option(
    "--gas-price-speed",
    "-gps",
    "gas_price_speed",
    help="gas price speed for eth gas station API",
    nargs=1,
    type=click.Choice(
        ["safeLow", "average", "fast", "fastest"],
        case_sensitive=True,
    ),
    default="fast",
)
@click.option(
    "-wp",
    "--wait-period",
    help="wait period between feed suggestion calls",
    nargs=1,
    type=int,
    default=7,
)
@click.option(
    "--rng-timestamp",
    "-rngts",
    "rng_timestamp",
    help="timestamp for Tellor RNG",
    nargs=1,
    type=int,
)
@click.option(
    "--oracle-address",
    "-oracle",
    "oracle_address",
    help="oracle contract address to interact with",
    nargs=1,
    type=str,
    default=None,
)
@click.option(
    "--autopay-address",
    "-autopay",
    "autopay_address",
    help="autopay contract address to interact with",
    nargs=1,
    type=str,
    default=None,
)
@click.option(
    "--diva-protocol",
    "-dpt",
    "reporting_diva_protocol",
    help="Report & settle DIVA Protocol derivative pools",
    default=False,
)
@click.option(
    "--diva-diamond-address",
    "-dda",
    "diva_diamond_address",
    help="DIVA Protocol contract address",
    nargs=1,
    type=click.UNPROCESSED,
    callback=validate_address,
    default=DIVA_DIAMOND_ADDRESS,
    prompt=False,
)
@click.option(
    "--diva-middleware-address",
    "-dma",
    "diva_middleware_address",
    help="DIVA Protocol middleware contract address",
    nargs=1,
    type=click.UNPROCESSED,
    callback=validate_address,
    default=DIVA_TELLOR_MIDDLEWARE_ADDRESS,
    prompt=False,
)
@click.option(
    "--custom-contract",
    "-custom",
    "custom_contract_reporter",
    help="Use a custom contract to report to oracle",
    nargs=1,
    default=None,
    type=str,
)
@click.option("--flex-360/--old-flex", default=True, help="Choose between tellor360 reporter or old flex")
@click.option("--binary-interface", "-abi", "abi", nargs=1, default=None, type=str)
@click.option("--rng-auto/--rng-auto-off", default=False)
@click.option("--submit-once/--submit-continuous", default=False)
@click.option("-pwd", "--password", type=str)
@click.option("-spwd", "--signature-password", type=str)
@click.pass_context
@async_run
async def report(
    ctx: Context,
    query_tag: str,
    build_feed: bool,
    tx_type: int,
    gas_limit: int,
    max_fee: Optional[int],
    priority_fee: Optional[int],
    legacy_gas_price: Optional[int],
    expected_profit: str,
    submit_once: bool,
    wait_period: int,
    gas_price_speed: str,
    reporting_diva_protocol: bool,
    diva_diamond_address: Optional[str],
    diva_middleware_address: Optional[str],
    rng_timestamp: int,
    password: str,
    signature_password: str,
    rng_auto: bool,
    oracle_address: str,
    autopay_address: str,
    custom_contract_reporter: Optional[str],
    abi: Optional[str],
    flex_360: bool,
) -> None:
    """Report values to Tellor oracle"""
    # Ensure valid user input for expected profit
    expected_profit = parse_profit_input(expected_profit)  # type: ignore
    if expected_profit is None:
        return

    if oracle_address:
        try:
            oracle_address = to_checksum_address(oracle_address)
        except ValueError:
            click.echo(f"contract address must be a hex string. Got: {oracle_address}")
            return

    if autopay_address:
        try:
            autopay_address = to_checksum_address(autopay_address)
        except ValueError:
            click.echo(f"contract address must be a hex string. Got: {autopay_address}")
            return

    assert tx_type in (0, 2)

    name = ctx.obj["ACCOUNT_NAME"]
    sig_acct_name = ctx.obj["SIGNATURE_ACCOUNT_NAME"]

    if sig_acct_name is not None:
        try:
            if not signature_password:
                signature_password = getpass.getpass(f"Enter password for {sig_acct_name} keyfile: ")
        except ValueError:
            click.echo("Invalid Password")

    # Initialize telliot core app using CLI context
    async with reporter_cli_core(ctx) as core:

        core._config, account = setup_config(core.config, account_name=name)

        endpoint = check_endpoint(core._config)

        if not endpoint or not account:
            click.echo("Accounts and/or endpoint unset.")
            click.echo(f"Account: {account}")
            click.echo(f"Endpoint: {core._config.get_endpoint()}")
            return

        # Make sure current account is unlocked
        if not account.is_unlocked:
            account.unlock(password)

        if sig_acct_name is not None:
            sig_account = find_accounts(name=sig_acct_name)[0]
            if not sig_account.is_unlocked:
                sig_account.unlock(password)
            sig_acct_addr = to_checksum_address(sig_account.address)
        else:
            sig_acct_addr = ""  # type: ignore

        cid = core.config.main.chain_id

        if custom_contract_reporter:
            try:
                custom_contract_reporter = to_checksum_address(custom_contract_reporter)
            except ValueError:
                click.echo(f"Contract address must be a hex string. Got: {custom_contract_reporter}")
                return
            if abi is None:
                try:
                    abi = ContractInfo(
                        name=None, org=None, address={int(core.config.main.chain_id): custom_contract_reporter}
                    ).get_abi(chain_id=core.config.main.chain_id)
                except Exception:
                    print("Unable to fetch contract abi, consider adding abi using -abi flag!")
                    return
            custom_contract = Contract(custom_contract_reporter, abi, core.endpoint, account)
            custom_contract.connect()

        # If we need to build a datafeed
        if build_feed:
            chosen_feed = build_feed_from_input()

            if chosen_feed is None:
                click.echo("Unable to build Datafeed from provided input")
                return

        # Use selected feed, or choose automatically
        elif query_tag is not None:
            try:
                chosen_feed: DataFeed[Any] = CATALOG_FEEDS[query_tag]  # type: ignore
            except KeyError:
                click.echo(f"No corresponding datafeed found for query tag: {query_tag}\n")
                return
        elif reporting_diva_protocol:
            if not valid_diva_chain(chain_id=cid):
                click.echo("Diva Protocol not supported for this chain")
                return
            chosen_feed = None
        elif rng_timestamp is not None:
            chosen_feed = await assemble_rng_datafeed(timestamp=rng_timestamp, node=core.endpoint, account=account)
        else:
            chosen_feed = None

        print_reporter_settings(
            signature_address=sig_acct_addr,
            query_tag=query_tag,
            transaction_type=tx_type,
            gas_limit=gas_limit,
            max_fee=max_fee,
            priority_fee=priority_fee,
            legacy_gas_price=legacy_gas_price,
            expected_profit=expected_profit,
            chain_id=cid,
            gas_price_speed=gas_price_speed,
            reporting_diva_protocol=reporting_diva_protocol,
        )

        _ = input("Press [ENTER] to confirm settings.")

        common_reporter_kwargs = {
            "endpoint": core.endpoint,
            "account": account,
            "datafeed": chosen_feed,
            "transaction_type": tx_type,
            "gas_limit": gas_limit,
            "max_fee": max_fee,
            "priority_fee": priority_fee,
            "legacy_gas_price": legacy_gas_price,
            "gas_price_speed": gas_price_speed,
            "chain_id": cid,
        }

        # Report to Polygon TellorFlex
        if core.config.main.chain_id in TELLOR_X_CHAINS and not flex_360:
            # Report to TellorX
            tellorx = core.get_tellorx_contracts()
            if oracle_address:
                tellorx.oracle.address = oracle_address
                tellorx.oracle.connect()

            tellorx_reporter_kwargs = {
                "master": tellorx.master,
                "oracle": tellorx.oracle,
                "expected_profit": expected_profit,
                **common_reporter_kwargs,
            }

            if sig_acct_addr != "":
                reporter = FlashbotsReporter(
                    signature_account=sig_account,
                    **tellorx_reporter_kwargs,
                )
            elif custom_contract_reporter:
                reporter = CustomXReporter(
                    custom_contract=custom_contract,
                    **tellorx_reporter_kwargs,
                )  # type: ignore
            else:
                reporter = IntervalReporter(**tellorx_reporter_kwargs)  # type: ignore

        else:

            stake = get_stake_amount()
            contracts = core.get_tellor360_contracts() if flex_360 else core.get_tellorflex_contracts()

            if oracle_address:
                contracts.oracle.address = oracle_address
                contracts.oracle.connect()

            if autopay_address:
                contracts.autopay.address = autopay_address
                contracts.autopay.connect()

            # Type 2 transactions unsupported currently
            common_reporter_kwargs["transaction_type"] = 0
            # set additional common kwargs to shorten code
            common_reporter_kwargs["oracle"] = contracts.oracle
            common_reporter_kwargs["autopay"] = contracts.autopay
            common_reporter_kwargs["token"] = contracts.token
            common_reporter_kwargs["stake"] = stake
            common_reporter_kwargs["expected_profit"] = expected_profit
            # selecting the right reporter will be changed after the switch
            if flex_360:
                if rng_auto:
                    reporter = RNGReporter(  # type: ignore
                        wait_period=120 if wait_period < 120 else wait_period,
                        **common_reporter_kwargs,
                    )
                elif reporting_diva_protocol:
                    diva_reporter_kwargs = {}
                    if diva_diamond_address is not None:
                        diva_reporter_kwargs["diva_diamond_address"] = diva_diamond_address
                    if diva_middleware_address is not None:
                        diva_reporter_kwargs["middleware_address"] = diva_middleware_address
                    reporter = DIVAProtocolReporter(
                        wait_period=wait_period,
                        **common_reporter_kwargs,
                        **diva_reporter_kwargs,  # type: ignore
                    )
                elif custom_contract_reporter:
                    reporter = CustomFlexReporter(
                        custom_contract=custom_contract,
                        wait_period=wait_period,
                        **common_reporter_kwargs,
                    )  # type: ignore
                else:
                    reporter = Tellor360Reporter(
                        wait_period=wait_period,
                        **common_reporter_kwargs,
                    )  # type: ignore
            else:
                reporter = TellorFlexReporter(
                    wait_period=wait_period,
                    **common_reporter_kwargs,
                )  # type: ignore

        if submit_once:
            _, _ = await reporter.report_once()
        else:
            await reporter.report()
