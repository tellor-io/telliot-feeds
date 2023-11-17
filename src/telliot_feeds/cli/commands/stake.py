from typing import Optional

import click
from click.core import Context
from eth_utils import to_checksum_address
from telliot_core.cli.utils import async_run

from telliot_feeds.cli.utils import common_options
from telliot_feeds.cli.utils import get_accounts_from_name
from telliot_feeds.cli.utils import reporter_cli_core
from telliot_feeds.reporters.stake import Stake
from telliot_feeds.utils.cfg import check_endpoint
from telliot_feeds.utils.cfg import setup_config
from telliot_feeds.utils.reporter_utils import has_native_token_funds


@click.group()
def deposit_stake() -> None:
    """Deposit tokens to the Tellor oracle."""
    pass


@deposit_stake.command()
@common_options
@click.option("--amount", "-amt", "amount", help="Amount of tokens to stake", nargs=1, type=float, required=True)
@click.pass_context
@async_run
async def stake(
    ctx: Context,
    account_str: str,
    amount: float,
    tx_type: int,
    gas_limit: int,
    base_fee_per_gas: Optional[float],
    priority_fee_per_gas: Optional[float],
    max_fee_per_gas: Optional[float],
    legacy_gas_price: Optional[int],
    password: str,
    min_native_token_balance: float,
    gas_multiplier: int,
    max_priority_fee_range: int,
    unsafe: bool,
) -> None:
    """Deposit tokens to oracle"""
    ctx.obj["ACCOUNT_NAME"] = account_str

    accounts = get_accounts_from_name(account_str)
    if not accounts:
        return

    ctx.obj["CHAIN_ID"] = accounts[0].chains[0]  # used in reporter_cli_core
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
        contracts.token._private_key = account.local_account.key
        # set private key for oracle stake deposit txn
        contracts.oracle._private_key = account.local_account.key

        if has_native_token_funds(
            to_checksum_address(account.address),
            core.endpoint.web3,
            min_balance=int(min_native_token_balance * 10**18),
        ):
            s = Stake(
                endpoint=core.endpoint,
                account=account,
                transaction_type=tx_type,
                gas_limit=gas_limit,
                legacy_gas_price=legacy_gas_price,
                gas_multiplier=gas_multiplier,
                max_priority_fee_range=max_priority_fee_range,
                priority_fee_per_gas=priority_fee_per_gas,
                base_fee_per_gas=base_fee_per_gas,
                max_fee_per_gas=max_fee_per_gas,
                oracle=contracts.oracle,
                token=contracts.token,
                min_native_token_balance=min_native_token_balance,
            )
            _ = await s.deposit_stake(int(amount * 1e18))
