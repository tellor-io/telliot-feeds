import getpass

import click
from click.core import Context
from telliot_core.cli.utils import async_run

from telliot_feeds.cli.utils import CustomHexBytes
from telliot_feeds.cli.utils import get_accounts_from_name
from telliot_feeds.cli.utils import reporter_cli_core
from telliot_feeds.cli.utils import valid_diva_chain
from telliot_feeds.integrations.diva_protocol.contract import DivaOracleTellorContract
from telliot_feeds.utils.log import get_logger

logger = get_logger(__name__)


@click.group()
def diva() -> None:
    """CLI commands for the DIVA Protocol integration."""
    pass


@diva.command()
@click.option(
    "--pool-id",
    "-pid",
    "pool_id",
    help="pool ID for Diva Protocol",
    nargs=1,
    type=CustomHexBytes,
    required=True,
)
@click.option(
    "--gas-price",
    "-gp",
    "legacy_gas_price",
    help="use custom legacy gasPrice (gwei)",
    nargs=1,
    type=int,
    required=False,
    default=100,
)
@click.option(
    "--account",
    "-a",
    "account_str",
    help="Name of account used for reporting, staking, etc. More info: run `telliot account --help`",
    required=True,
    nargs=1,
    type=str,
)
@click.option("-pswd", "--password", type=str)
@click.pass_context
@async_run
async def settle(
    ctx: Context,
    account_str: str,
    pool_id: CustomHexBytes,
    password: str,
    legacy_gas_price: int,
) -> None:
    """Settle a derivative pool in DIVA Protocol."""
    ctx.obj["ACCOUNT_NAME"] = account_str
    accounts = get_accounts_from_name(account_str)
    if not accounts:
        return
    ctx.obj["CHAIN_ID"] = accounts[0].chains[0]
    try:
        if not password:
            password = getpass.getpass(f"Enter password for {account_str} keyfile: ")
    except ValueError:
        click.echo("Invalid Password")

    # Initialize telliot core app using CLI context
    async with reporter_cli_core(ctx) as core:

        # Make sure current account is unlocked
        account = core.get_account()
        if not account.is_unlocked:
            account.unlock(password)

        cid = core.config.main.chain_id
        if not valid_diva_chain(chain_id=cid):
            return

        oracle = DivaOracleTellorContract(core.endpoint, account)
        oracle.connect()

        status = await oracle.set_final_reference_value(pool_id=pool_id.hex(), legacy_gas_price=legacy_gas_price)
        if status is not None and status.ok:
            click.echo(f"Pool {pool_id.hex()} settled.")
        else:
            click.echo(f"Unable to settle Pool {pool_id.hex()}.")
