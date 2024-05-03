from typing import List
from typing import Optional
from typing import Tuple

import click
from chained_accounts import ChainedAccount
from chained_accounts import find_accounts
from simple_term_menu import TerminalMenu
from telliot_core.apps.core import Tellor360OracleContract
from telliot_core.apps.telliot_config import TelliotConfig
from telliot_core.model.endpoints import RPCEndpoint

from telliot_feeds.utils.log import get_logger


logger = get_logger(__name__)
API_KEY = TelliotConfig().api_keys.find(name="coingecko")[0].key


def setup_config(
    cfg: TelliotConfig, account_name: str, unsafe: bool = False
) -> Tuple[TelliotConfig, Optional[ChainedAccount]]:
    """Setup TelliotConfig via CLI if not already configured

    Inputs:
    - cfg (TelliotConfig) -- current Telliot configuration

    Returns:
    - TelliotConfig -- updated Telliot configuration post-setup
    - ChainedAccount -- account configuration to choose as current account
    """

    if cfg is None:
        cfg = TelliotConfig()

    accounts = check_accounts(cfg, account_name)
    endpoint = check_endpoint(cfg)

    click.echo(
        """
         █████            ██        █████
       ██     ██        ██        ██     ██
     ██         ██    ██  ██    ██         ██
     ██         ██  ██      ██  ██         ██
       ██         ██          ██         ██
         ██                            ██
         ██                            ██
       ██                                ██
       ██                                ██
     ████████████████████████████  ██████████
     ████████████████████████████  ██████████
     ████████████████████████████  ██████████
     ████████████████████████████  ██████████
       ██                                ██
       ██           ██████████           ██
       ██             ██████             ██
         ██                            ██
           ██                        ██
             ██                    ██
               ██                ██
                 ████████████████

██████  █████  ██     ██     ██████  ██████  ██████
  ██    ███    ██     ██       ██    ██  ██    ██
  ██    █████  █████  █████  ██████  ██████    ██

            """
    )
    click.echo(f"Your current settings...\nYour chain id: {cfg.main.chain_id}")
    click.echo(f"Oracle contract address: {check_oracle_address(cfg, account_name)}\n")
    if API_KEY == "":
        click.echo(
            "Coin Gecko API key not found in api_keys.yaml.\n"
            "Using public API for Coin Gecko prices (rate limits apply)\n"
        )
    else:
        click.echo("Using API key for Coin Gecko prices\n")

    if endpoint is not None:
        click.echo(
            f"Your {endpoint.network} endpoint: \n"
            f" - provider: {endpoint.provider}\n"
            f" - RPC url: {endpoint.url}\n"
            f" - explorer url: {endpoint.explorer}"
        )
    else:
        click.echo("No endpoints set.")

    if accounts:
        click.echo(f"Your account: {accounts[0].name} at address {accounts[0].address}")

    else:
        click.echo("No accounts set.")

    if unsafe:
        keep_settings = True
    else:
        keep_settings = click.confirm("Proceed with current settings (y) or update (n)?", default=True)

    if keep_settings:
        click.echo("Keeping current settings...")
        return cfg, accounts[0] if accounts else None

    if unsafe:
        want_to_update_chain_id = False
    else:
        want_to_update_chain_id = click.confirm(f"Chain_id is {cfg.main.chain_id}. Do you want to update it?")

    if want_to_update_chain_id:  # noqa: F821
        new_chain_id = click.prompt("Enter a new chain id", type=int)
        cfg.main.chain_id = new_chain_id

    new_endpoint = setup_endpoint(cfg, cfg.main.chain_id)
    if new_endpoint is not None:
        cfg.endpoints.endpoints.insert(0, new_endpoint)
        click.echo(f"{new_endpoint} added!")

    click.echo(f"Your account name: {accounts[0].name if accounts else None}")

    new_account = setup_account(cfg.main.chain_id)
    if new_account is not None:
        click.echo(f"{new_account.name} selected!")

    # write new endpoints to file (note: accounts are automatically written to file)
    cfg._ep_config_file.save_config(cfg.endpoints)

    return cfg, new_account


def setup_endpoint(cfg: TelliotConfig, chain_id: int) -> RPCEndpoint:
    """Setup Endpoints via CLI if not already configured"""

    endpoint = check_endpoint(cfg)

    if endpoint is not None:
        keep = click.confirm(f"Do you want to use this endpoint on chain_id {chain_id}?")
        if keep:
            return endpoint
        else:
            return prompt_for_endpoint(chain_id)

    else:
        click.echo(f"No endpoints are available for chain_id {chain_id}. Please add one:")
        return prompt_for_endpoint(chain_id)


def check_endpoint(cfg: TelliotConfig) -> Optional[RPCEndpoint]:
    """Check if there is a pre-set endpoint in the config"""

    try:
        return cfg.get_endpoint()
    except Exception as e:
        logger.warning("No endpoints found: " + str(e))
        return None


def check_accounts(cfg: TelliotConfig, account_name: str) -> List[ChainedAccount]:
    """Check if there is a pre-set account in the config"""

    return find_accounts(chain_id=cfg.main.chain_id, name=account_name)  # type: ignore


def check_oracle_address(cfg: TelliotConfig, account_name: str) -> Optional[str]:
    """Check oracle contract for the account's chain ID"""

    try:
        return str(Tellor360OracleContract(node=check_endpoint(cfg), account=account_name).address)
    except Exception as e:
        logger.warning(f"No oracle contract found on chain id{cfg.main.chain_id}: " + str(e))
        return None


def prompt_for_endpoint(chain_id: int) -> Optional[RPCEndpoint]:
    """Take user input to create a new RPCEndpoint"""
    rpc_url = click.prompt("Enter RPC URL", type=str)
    explorer_url = click.prompt("Enter block explorer URL", type=str)

    try:
        return RPCEndpoint(chain_id, "n/a", "n/a", rpc_url, explorer_url)
    except Exception as e:
        click.echo("Cannot add endpoint: invalid endpoint properties" + str(e))
        return None


def setup_account(chain_id: int) -> Optional[ChainedAccount]:
    """Set up ChainedAccount for TelliotConfig if not already configured"""

    accounts = find_accounts(chain_id=chain_id)
    if accounts is None:
        return prompt_for_account(chain_id)

    else:
        title = f"You have these accounts on chain_id {chain_id}"
        options = [a.name + " " + a.address for a in accounts] + ["add account..."]

        menu = TerminalMenu(options, title=title)
        selected_index = menu.show()

        if options[selected_index] == "add account...":
            return prompt_for_account(chain_id=chain_id)
        else:
            selected_account = accounts[selected_index]
            click.echo(f"Account {selected_account.name} at {selected_account.address} selected.")
            return selected_account


def prompt_for_account(chain_id: int) -> Optional[ChainedAccount]:
    """take user input to create a new ChainedAccount account for the Telliot Config"""

    acc_name = click.prompt("Enter account name", type=str)
    private_key = click.prompt("Enter private key", type=str)
    chain_id = click.prompt("Enter chain id", type=int)

    try:
        return ChainedAccount.add(acc_name, chain_id, private_key, password=None)
    except Exception as e:
        if "already exists" in str(e):
            click.echo(f"Cannot add account: Account {acc_name} already exists :)" + str(e))
        else:
            click.echo("Cannot add account: Invalid account properties" + str(e))
        return None
