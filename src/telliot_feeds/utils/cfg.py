from typing import List
from typing import Optional

import click
from chained_accounts import ChainedAccount
from chained_accounts import find_accounts
from simple_term_menu import TerminalMenu
from telliot_core.apps.telliot_config import TelliotConfig
from telliot_core.model.endpoints import RPCEndpoint

from telliot_feeds.utils.log import get_logger


logger = get_logger(__name__)


def setup_config(cfg: TelliotConfig) -> TelliotConfig:
    """Setup TelliotConfig via CLI if not already configured"""

    if cfg is None:
        cfg = TelliotConfig()

    want_to_update = click.confirm(f"Chain_id is {cfg.main.chain_id}. Do you want to update it?")

    if want_to_update:  # noqa: F821
        new_chain_id = click.prompt("Enter a new chain id", type=int)
        cfg.main.chain_id = new_chain_id

    accounts = check_accounts(cfg)
    endpoint = check_endpoint(cfg)

    # if configs are setup...
    # print current settings of cfg
    # if accounts is not None and endpoint is not None:
    click.echo(
        f"Your current configuration...\n"
        f"Your chain id: {cfg.main.chain_id}\n"
        f"Your endpoint: {endpoint}\n"
        f"Your account name: {accounts[0].name}"
    )

    new_endpoint = setup_endpoint(cfg, cfg.main.chain_id)

    if new_endpoint is not None:
        cfg.endpoints.endpoints.insert(0, new_endpoint)
        click.echo(f"{new_endpoint} added!")

    new_account = setup_account(cfg.main.chain_id)
    if new_account is not None:
        click.echo(f"{new_account} added!")

    return cfg


def setup_endpoint(cfg: TelliotConfig, chain_id: int) -> RPCEndpoint:
    """Setup Endpoints via CLI if not already configured"""
    # pass
    # if test config...
    #     check for and add the test endpoint
    # else...
    #     check if any endpoints available for the chain_id

    endpoint = check_endpoint(cfg)

    #     print settings if there are endpoints available
    if endpoint is not None:
        keep = click.confirm(
            f"This endpoint is available for chain_id {chain_id}: {str(endpoint)}. Do you want to use it?"
        )

        if keep:

            return endpoint

        else:

            return prompt_for_endpoint(chain_id)

    else:

        return prompt_for_endpoint(chain_id)


def check_endpoint(cfg: TelliotConfig) -> Optional[RPCEndpoint]:
    """Check if there is a pre-set endpoint in the config"""

    try:
        return cfg.get_endpoint()
    except Exception:
        return None


def check_accounts(cfg: TelliotConfig) -> List[ChainedAccount]:
    """Check if there is a pre-set account in the config"""

    return find_accounts(chain_id=cfg.main.chain_id)  # type: ignore


def prompt_for_endpoint(chain_id: int) -> Optional[RPCEndpoint]:

    network_name = click.prompt("Enter network name: ", type=str)
    provider = click.prompt("Enter Provider: ", type=str)
    rpc_url = click.prompt("Enter RPC url", type=str)
    explorer_url = click.prompt("Enter Explorer url: ", type=str)

    try:
        return RPCEndpoint(chain_id, network_name, provider, rpc_url, explorer_url)
    except Exception:
        click.echo("Cannot add endpoint: invalid endpoint properties")
        return None


def setup_account(chain_id: int) -> Optional[ChainedAccount]:
    """Set up ChainedAccount for TelliotConfig if not already configured"""

    # find account
    accounts = find_accounts(chain_id=chain_id)
    # if no account found...
    if accounts is None:
        return prompt_for_account(chain_id)

    # if account(s) found...
    else:
        # pick an account
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

    # prompt for account
    # account name
    acc_name = click.prompt("Enter account name: ", type=str)
    # private key
    private_key = click.prompt("Enter private key: ", type=str)
    # chain id
    chain_id = click.prompt("Enter chain id: ", type=int)
    # add account
    try:
        return ChainedAccount.add(acc_name, chain_id, private_key, password=None)
    except Exception as e:
        if "already exists" in str(e):
            click.echo(f"Cannot add account: Account {acc_name} already exists :)")
        else:
            click.echo("Cannot add account: Invalid account properties")
        return None
