from typing import Optional

import click
from click.core import Context
from telliot_core.cli.utils import async_run

from telliot_feeds.cli.utils import call_oracle
from telliot_feeds.cli.utils import common_options
from telliot_feeds.cli.utils import get_accounts_from_name


@click.group()
def request_withdraw_stake() -> None:
    """Request to withdraw tokens from the Tellor oracle which locks them for 7 days."""
    pass


@request_withdraw_stake.command()
@common_options
@click.option(
    "--amount", "-amt", "amount", help="Amount of tokens to request withdraw", nargs=1, type=float, required=True
)
@click.pass_context
@async_run
async def request_withdraw(
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
    """Request withdraw of tokens from oracle"""
    ctx.obj["ACCOUNT_NAME"] = account_str

    accounts = get_accounts_from_name(account_str)
    if not accounts:
        return

    ctx.obj["CHAIN_ID"] = accounts[0].chains[0]  # used in reporter_cli_core

    user_inputs = {
        "password": password,
        "min_native_token_balance": min_native_token_balance,
        "gas_limit": gas_limit,
        "base_fee_per_gas": base_fee_per_gas,
        "priority_fee_per_gas": priority_fee_per_gas,
        "max_fee_per_gas": max_fee_per_gas,
        "legacy_gas_price": legacy_gas_price,
        "transaction_type": tx_type,
        "gas_multiplier": gas_multiplier,
        "max_priority_fee_range": max_priority_fee_range,
    }
    await call_oracle(ctx=ctx, func="requestStakingWithdraw", user_inputs=user_inputs, _amount=int(amount * 1e18))
