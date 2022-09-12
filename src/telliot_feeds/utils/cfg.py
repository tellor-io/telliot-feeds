import os
from typing import Optional

import click
from chained_accounts import ChainedAccount
from chained_accounts import find_accounts
from telliot_core.apps.telliot_config import TelliotConfig

from telliot_feeds.utils.log import get_logger


logger = get_logger(__name__)


def mainnet_config() -> Optional[TelliotConfig]:
    cfg = TelliotConfig()
    cfg.main.chain_id = 1
    endpoint = cfg.get_endpoint()

    if "INFURA_API_KEY" in endpoint.url:
        endpoint.url = f'wss://mainnet.infura.io/ws/v3/{os.environ["INFURA_API_KEY"]}'

    accounts = find_accounts(chain_id=1)
    if not accounts:
        # Create a test account using PRIVATE_KEY defined on github.
        key = os.getenv("PRIVATE_KEY", None)
        if key:
            ChainedAccount.add("git-mainnet-key", chains=1, key=os.environ["PRIVATE_KEY"], password="")
        else:
            logger.warning("No mainnet account added!")
            return None

    return cfg


def setup_account(cfg: TelliotConfig, account_name: Optional[str]) -> TelliotConfig:
    """Setup account via CLI if not already configured"""

    # check if configs are setup
    # prompt the user to select a differnt chain id
    # prompt the user to add a chained account
    # add...
    # account name
    # private key

    # if testing...
    #     add test account with .env private key
    # else:
    #     account_found = False
    #     for i in supported chains:
    #         find accounts of i
    #     if multiple accounts FOUND...
    #         select one or overwrite
    #     else if one account found...
    #         select it or overwrite
    #     else not accounts:
    #         prompt with click to add an account. we need to add:
    #             account name
    #             private key

    # accounts = find_accounts(chain_id=chain_id)
    # if not accounts:
    #     # Create a test account using PRIVATE_KEY defined on github.
    #     key = os.getenv("PRIVATE_KEY", None)
    #     if key:
    #         ChainedAccount.add(account_name, chains=chain_id, key=os.environ["PRIVATE_KEY"], password="")
    #     else:
    #         input(f"We need an account on chain_id {chain_id}.")

    # return cfg
    pass


def setup_endpoint(cfg: TelliotConfig, chain_id: int):
    """Setup Endpoints via CLI if not already configured"""
    pass
    # if test config...
    #     check for and add the test endpoint
    # else...
    #     check if any endpoints available for the chain_id
    #     print settings if there are endpoints available
    #     if multiple are available...
    #         choose one or overwritee
    #     else if one is available
    #         choose it or overwrite
    #     else
    #         prompt user for...
    #             network name
    #             testnet or mainnet
    #             provider
    #             rpc url
    #             explorer url

    # if "INFURA_API_KEY" in endpoint.url:
    #     endpoint.url = f'wss://mainnet.infura.io/ws/v3/{os.environ["INFURA_API_KEY"]}'


def print_current_config(cfg: TelliotConfig = None) -> None:
    """Print the current config settings"""
    if cfg is None:
        cfg = TelliotConfig()
    click.echo(f"Chain ID: {cfg.main.chain_id}")
    click.echo(f"Endpoint: {cfg.get_endpoint()}")
    click.echo(f"Account: {cfg.get_account()}")


def write_configs(cfg: TelliotConfig) -> None:
    """Update the current config settings in their respective files"""
    pass


def update_current_config(cfg: TelliotConfig = None) -> TelliotConfig:
    """Update the current config settings"""
    if cfg is None:
        cfg = TelliotConfig()

    # keep current config settings
    print_current_config(cfg=cfg)
    if click.confirm("Do you want to use the current config settings?"):
        return cfg

    # update current config settings
    chain_id = click.prompt("What chain ID do you want to use?", type=int)
    # list available accounts for the chain_id
    # if none available...
    # prompt user to add an account
    # if multiple available...
    # prompt user to select one or add a new one
    # list available endpoints for the chain_id
    # if none available...
    # prompt user to add an endpoint
    # if multiple available...
    # prompt user to select one or add a new one

    # write the new config settings to the config files
    write_configs(cfg=cfg)

    return cfg
