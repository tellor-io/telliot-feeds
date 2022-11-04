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
from telliot_feeds.cli.utils import get_stake_amount
from telliot_feeds.cli.utils import print_reporter_settings
from telliot_feeds.cli.utils import parse_profit_input
from telliot_feeds.datafeed import DataFeed
from telliot_feeds.feeds import CATALOG_FEEDS
from telliot_feeds.feeds.tellor_rng_feed import assemble_rng_datafeed
from telliot_feeds.integrations.diva_protocol import DIVA_DIAMOND_ADDRESS
from telliot_feeds.integrations.diva_protocol import DIVA_TELLOR_MIDDLEWARE_ADDRESS
from telliot_feeds.integrations.diva_protocol.report import DIVAProtocolReporter
from telliot_feeds.queries.query_catalog import query_catalog
from telliot_feeds.reporters.rng_interval import RNGReporter
from telliot_feeds.reporters.tellor_360 import Tellor360Reporter
from telliot_feeds.reporters.tellorflex import TellorFlexReporter
from telliot_feeds.utils.cfg import check_endpoint
from telliot_feeds.utils.cfg import setup_config
from telliot_feeds.utils.log import get_logger


logger = get_logger(__name__)


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
    type=Union[click.Choice(["YOLO"]), float],
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
    "--custom-token-contract",
    "-custom-token",
    "custom_token_contract",
    help="Address of custom token contract",
    nargs=1,
    default=None,
    type=click.UNPROCESSED,
    callback=validate_address,
    prompt=False,
)
@click.option(
    "--custom-oracle-contract",
    "-custom-oracle",
    "custom_oracle_contract",
    help="Address of custom oracle contract",
    nargs=1,
    default=None,
    type=click.UNPROCESSED,
    callback=validate_address,
    prompt=False,
)
@click.option(
    "--custom-autopay-contract",
    "-custom-autopay",
    "custom_autopay_contract",
    help="Address of custom autopay contract",
    nargs=1,
    default=None,
    type=click.UNPROCESSED,
    callback=validate_address,
    prompt=False,
)
@click.option("--tellor-360/--tellor-flex", "-360/-flex", "tellor_360", default=True, help="Choose between Tellor 360 or Flex contracts")
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
    custom_token_contract: Optional[str],
    custom_oracle_contract: Optional[str],
    custom_autopay_contract: Optional[str],
    abi: Optional[str],
    tellor_360: bool,
) -> None:
    """Report values to Tellor oracle"""
    # Ensure valid user input for expected profit
    expected_profit = parse_profit_input(expected_profit)  # type: ignore
    if expected_profit is None:
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
            if not valid_diva_chain(chain_id=core.config.main.chain_id):
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
            chain_id=core.config.main.chain_id,
            gas_price_speed=gas_price_speed,
            reporting_diva_protocol=reporting_diva_protocol,
        )

        _ = input("Press [ENTER] to confirm settings.")

        stake = get_stake_amount()

        contracts = core.get_tellor360_contracts() if tellor_360 else core.get_tellorflex_contracts()

        if custom_oracle_contract:
            contracts.oracle.address = custom_oracle_contract
            contracts.oracle.connect()

        if custom_autopay_contract:
            contracts.autopay.address = custom_autopay_contract
            contracts.autopay.connect()
        
        if custom_token_contract:
            contracts.token.address = custom_token_contract
            contracts.token.connect()

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
            "chain_id": core.config.main.chain_id,
            "wait_period": wait_period,
            "oracle": contracts.oracle,
            "autopay": contracts.autopay,
            "token": contracts.token,
            "expected_profit": expected_profit,
            "stake": stake,
            "transaction_type": 0, # TODO: Remove this, type 2 transactions are not supported currently
        }
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
                    **common_reporter_kwargs,
                    **diva_reporter_kwargs,  # type: ignore
                )
            else:
                reporter = Tellor360Reporter(
                    **common_reporter_kwargs,
                )  # type: ignore
        else:
            reporter = TellorFlexReporter(
                **common_reporter_kwargs,
            )  # type: ignore

        if submit_once:
            _, _ = await reporter.report_once()
        else:
            await reporter.report()
