from typing import Any
from typing import Optional
from typing import Union

import click
from chained_accounts import find_accounts
from click.core import Context
from eth_typing import ChecksumAddress
from eth_utils import to_checksum_address
from telliot_core.cli.utils import async_run

from telliot_feeds.cli.utils import build_feed_from_input
from telliot_feeds.cli.utils import common_options
from telliot_feeds.cli.utils import common_reporter_options
from telliot_feeds.cli.utils import get_accounts_from_name
from telliot_feeds.cli.utils import print_reporter_settings
from telliot_feeds.cli.utils import reporter_cli_core
from telliot_feeds.cli.utils import valid_diva_chain
from telliot_feeds.cli.utils import validate_address
from telliot_feeds.datafeed import DataFeed
from telliot_feeds.feeds import CATALOG_FEEDS
from telliot_feeds.feeds.tellor_rng_feed import assemble_rng_datafeed
from telliot_feeds.integrations.diva_protocol import DIVA_DIAMOND_ADDRESS
from telliot_feeds.integrations.diva_protocol import DIVA_TELLOR_MIDDLEWARE_ADDRESS
from telliot_feeds.integrations.diva_protocol.report import DIVAProtocolReporter
from telliot_feeds.reporters.flashbot import FlashbotsReporter
from telliot_feeds.reporters.rng_interval import RNGReporter
from telliot_feeds.reporters.tellor_360 import Tellor360Reporter
from telliot_feeds.utils.cfg import check_endpoint
from telliot_feeds.utils.cfg import setup_config
from telliot_feeds.utils.log import get_logger
from telliot_feeds.utils.reporter_utils import create_custom_contract
from telliot_feeds.utils.reporter_utils import prompt_for_abi


logger = get_logger(__name__)


@click.group()
def reporter() -> None:
    """Report data on-chain."""
    pass


@click.option(
    "--signature-account",
    "-sa",
    "signature_account",
    help="Name of signature account used for reporting with Flashbots.",
    required=False,
    nargs=1,
    type=str,
)
@reporter.command()
@common_options
@common_reporter_options
@click.option(
    "--build-feed",
    "-b",
    "build_feed",
    help="build a datafeed from a query type and query parameters",
    is_flag=True,
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
@click.option(
    "--random-feeds/--no-random-feeds",
    "-rf/-nrf",
    "use_random_feeds",
    default=False,
    help="Reporter will use a random datafeed from the catalog.",
)
@click.option("--rng-auto/--rng-auto-off", default=False)
@click.option("-spwd", "--signature-password", type=str)
@click.option(
    "--ignore-tbr/--include-tbr",
    help="optionaly ignore time based rewards in profit calculations. relevant only on eth-mainnet/eth-testnets",
    default=False,
)
@click.pass_context
@async_run
async def report(
    ctx: Context,
    query_tag: str,
    build_feed: bool,
    tx_type: int,
    gas_limit: int,
    base_fee_per_gas: Optional[float],
    priority_fee_per_gas: Optional[float],
    max_fee_per_gas: Optional[float],
    legacy_gas_price: Optional[int],
    expected_profit: str,
    submit_once: bool,
    wait_period: int,
    reporting_diva_protocol: bool,
    diva_diamond_address: Optional[str],
    diva_middleware_address: Optional[str],
    rng_timestamp: int,
    password: str,
    signature_password: str,
    rng_auto: bool,
    min_native_token_balance: float,
    custom_token_contract: Optional[ChecksumAddress],
    custom_oracle_contract: Optional[ChecksumAddress],
    custom_autopay_contract: Optional[ChecksumAddress],
    stake: float,
    account_str: str,
    signature_account: str,
    check_rewards: bool,
    use_random_feeds: bool,
    gas_multiplier: int,
    max_priority_fee_range: int,
    ignore_tbr: bool,
    unsafe: bool,
    skip_manual_feeds: bool,
) -> None:
    """Report values to Tellor oracle"""
    ctx.obj["ACCOUNT_NAME"] = account_str
    ctx.obj["SIGNATURE_ACCOUNT_NAME"] = signature_account

    accounts = get_accounts_from_name(account_str)
    if not accounts:
        return

    ctx.obj["CHAIN_ID"] = accounts[0].chains[0]  # used in reporter_cli_core
    # Initialize telliot core app using CLI context
    async with reporter_cli_core(ctx) as core:

        core._config, account = setup_config(core.config, account_name=account_str, unsafe=unsafe)

        endpoint = check_endpoint(core._config)

        if not endpoint or not account:
            click.echo("Accounts and/or endpoint unset.")
            click.echo(f"Account: {account}")
            click.echo(f"Endpoint: {core._config.get_endpoint()}")
            return

        # Make sure current account is unlocked
        if not account.is_unlocked:
            account.unlock(password)

        if signature_account is not None:
            sig_account = find_accounts(name=signature_account)[0]
            if not sig_account.is_unlocked:
                sig_account.unlock(signature_password)
            sig_acct_addr = to_checksum_address(sig_account.address)
        else:
            sig_acct_addr = ""

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
            chosen_feed = await assemble_rng_datafeed(timestamp=rng_timestamp)
        else:
            chosen_feed = None

        print_reporter_settings(
            signature_address=sig_acct_addr,
            query_tag=query_tag,
            transaction_type=tx_type,
            gas_limit=gas_limit,
            max_fee=base_fee_per_gas,
            priority_fee=priority_fee_per_gas,
            base_fee=base_fee_per_gas,
            legacy_gas_price=legacy_gas_price,
            expected_profit=expected_profit,
            chain_id=core.config.main.chain_id,
            reporting_diva_protocol=reporting_diva_protocol,
            stake_amount=stake,
            min_native_token_balance=min_native_token_balance,
        )

        if not unsafe:
            _ = input("Press [ENTER] to confirm settings.")

        contracts = core.get_tellor360_contracts()

        if custom_oracle_contract:
            contracts.oracle.connect()  # set telliot_core.contract.Contract.contract attribute
            custom_oracle_abi = prompt_for_abi()
            contracts.oracle = create_custom_contract(
                original_contract=contracts.oracle,
                custom_contract_addr=custom_oracle_contract,
                custom_abi=custom_oracle_abi,
                endpoint=core.endpoint,
                account=account,
            )
            contracts.oracle.connect()

        if custom_autopay_contract:
            contracts.autopay.connect()  # set telliot_core.contract.Contract.contract attribute
            custom_autopay_abi = prompt_for_abi()
            contracts.autopay = create_custom_contract(
                original_contract=contracts.autopay,
                custom_contract_addr=custom_autopay_contract,
                custom_abi=custom_autopay_abi,
                endpoint=core.endpoint,
                account=account,
            )
            contracts.autopay.connect()

        if custom_token_contract:
            contracts.token.connect()  # set telliot_core.contract.Contract.contract attribute
            custom_token_abi = prompt_for_abi()
            contracts.token = create_custom_contract(
                original_contract=contracts.token,
                custom_contract_addr=custom_token_contract,
                custom_abi=custom_token_abi,
                endpoint=core.endpoint,
                account=account,
            )
            contracts.token.connect()

        common_reporter_kwargs = {
            "endpoint": core.endpoint,
            "account": account,
            "datafeed": chosen_feed,
            "gas_limit": gas_limit,
            "base_fee_per_gas": base_fee_per_gas,
            "priority_fee_per_gas": priority_fee_per_gas,
            "max_fee_per_gas": max_fee_per_gas,
            "legacy_gas_price": legacy_gas_price,
            "chain_id": core.config.main.chain_id,
            "wait_period": wait_period,
            "oracle": contracts.oracle,
            "autopay": contracts.autopay,
            "token": contracts.token,
            "expected_profit": expected_profit,
            "stake": stake,
            "transaction_type": tx_type,
            "min_native_token_balance": int(min_native_token_balance * 10**18),
            "check_rewards": check_rewards,
            "use_random_feeds": use_random_feeds,
            "gas_multiplier": gas_multiplier,
            "max_priority_fee_range": max_priority_fee_range,
            "ignore_tbr": ignore_tbr,
            "skip_manual_feeds": skip_manual_feeds,
        }
        reporter: Union[FlashbotsReporter, RNGReporter, Tellor360Reporter]
        if sig_acct_addr:
            reporter = FlashbotsReporter(
                signature_account=sig_account,
                **common_reporter_kwargs,
            )
        elif rng_auto:
            common_reporter_kwargs["wait_period"] = 120 if wait_period < 120 else wait_period
            reporter = RNGReporter(
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
            )

        if submit_once:
            _, _ = await reporter.report_once()
        else:
            await reporter.report()
