from typing import Optional

import click
from click.core import Context
from eth_utils import to_checksum_address
from telliot_core.cli.utils import async_run

from telliot_feeds.cli.utils import get_accounts_from_name
from telliot_feeds.cli.utils import reporter_cli_core
from telliot_feeds.cli.utils import valid_transaction_type
from telliot_feeds.reporters.tellor_360 import Tellor360Reporter
from telliot_feeds.utils.cfg import check_endpoint
from telliot_feeds.utils.cfg import setup_config
from telliot_feeds.utils.reporter_utils import has_native_token_funds


@click.group()
def deposit_stake() -> None:
    """Deposit tokens to the Tellor oracle."""
    pass


@click.option(
    "--account",
    "-a",
    "account_str",
    help="Name of account used for reporting, staking, etc. More info: run `telliot account --help`",
    required=True,
    nargs=1,
    type=str,
)
@click.option("--amount", "-amt", "amount", help="Amount of tokens to stake", nargs=1, type=float, required=True)
@click.option(
    "--gas-limit",
    "-gl",
    "gas_limit",
    help="use custom gas limit",
    nargs=1,
    type=int,
)
@click.option(
    "--max-fee",
    "-mf",
    "max_fee",
    help="use custom maxFeePerGas (gwei)",
    nargs=1,
    type=float,
    required=False,
)
@click.option(
    "--priority-fee",
    "-pf",
    "priority_fee",
    help="use custom maxPriorityFeePerGas (gwei)",
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
    help="increase gas price by this percentage (default 1%) ie 5 = 5%",
    nargs=1,
    type=int,
    default=1,  # 1% above the gas price by web3
)
@click.option(
    "--max-priority-fee-range",
    "-mpfr",
    "max_priority_fee_range",
    help="the maximum range of priority fees to use in gwei (default 80 gwei)",
    nargs=1,
    type=int,
    default=80,  # 80 gwei
)
@click.option("-pwd", "--password", type=str)
@deposit_stake.command()
@click.pass_context
@async_run
async def stake(
    ctx: Context,
    account_str: str,
    amount: float,
    tx_type: int,
    gas_limit: int,
    max_fee: Optional[float],
    priority_fee: Optional[float],
    legacy_gas_price: Optional[int],
    password: str,
    min_native_token_balance: float,
    gas_multiplier: int,
    max_priority_fee_range: int,
) -> None:
    """Deposit tokens to oracle"""
    ctx.obj["ACCOUNT_NAME"] = account_str

    accounts = get_accounts_from_name(account_str)
    if not accounts:
        return

    ctx.obj["CHAIN_ID"] = accounts[0].chains[0]  # used in reporter_cli_core
    # if max_fee flag is set, then priority_fee must also be set
    if (max_fee is not None and priority_fee is None) or (max_fee is None and priority_fee is not None):
        raise click.UsageError("Must specify both max fee and priority fee")
    # Initialize telliot core app using CLI context
    async with reporter_cli_core(ctx) as core:

        core._config, account = setup_config(core.config, account_name=account_str)

        endpoint = check_endpoint(core._config)

        if not endpoint or not account:
            click.echo("Accounts and/or endpoint unset.")
            click.echo(f"Account: {account}")
            click.echo(f"Endpoint: {core._config.get_endpoint()}")
            return

        # Make sure current account is unlocked
        if not account.is_unlocked:
            account.unlock(password)

        contracts = core.get_tellor360_contracts()
        # set private key for token approval txn via token contract
        contracts.token._private_key = account.local_account.privateKey
        # set private key for oracle stake deposit txn
        contracts.oracle._private_key = account.local_account.privateKey

        common_reporter_kwargs = {
            "endpoint": core.endpoint,
            "account": account,
            "gas_limit": gas_limit,
            "max_fee": max_fee,
            "priority_fee": priority_fee,
            "legacy_gas_price": legacy_gas_price,
            "chain_id": core.config.main.chain_id,
            "transaction_type": tx_type,
            "gas_multiplier": gas_multiplier,
            "max_priority_fee_range": max_priority_fee_range,
            "oracle": contracts.oracle,
            "autopay": contracts.autopay,
            "token": contracts.token,
        }
        if has_native_token_funds(
            to_checksum_address(account.address),
            core.endpoint.web3,
            min_balance=int(min_native_token_balance * 10**18),
        ):
            _ = await Tellor360Reporter(**common_reporter_kwargs).deposit_stake(int(amount * 1e18))
