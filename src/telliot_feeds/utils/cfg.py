from typing import Optional

import click

from chained_accounts import ChainedAccount
from chained_accounts import find_accounts
from telliot_core.apps.telliot_config import TelliotConfig
from telliot_core.model.endpoints import RPCEndpoint


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

def setup_account(cfg:TelliotConfig, account_name: Optional[str]) -> TelliotConfig:
    """Setup account via CLI if not already configured"""

    choice = input(f"Chain_id is {cfg.main.chain_id}. Do you want to update it? (y/n)")

    if choice.lower() == "y":
        new_chain_id = input("Enter a new chain id")    # chck if confings are setup
        cfg.main.chain_id = new_chain_id

    config_is_setup = check_config(cfg)
    # if configs are setup...
         # print current settings of cfg
    if config_is_setup:
        click.echo(
            f"Your current configuration...\n"
            f"Chain id is {cfg.main.chain_id}\n"
            f"Endpoint {cfg.get_endpoint()}\n"
            f"Account {find_accounts(chain_id=cfg.main.chain_id)}"
        )

    choice = input("Do you want to change the Endpoints? (y/n)")

    # if not..
    
    #prompt the user to add a chained account
    #add...
        #account name
        #private key

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


def setup_endpoint(cfg:TelliotConfig, chain_id:int) -> TelliotConfig:
    """Setup Endpoints via CLI if not already configured"""
    # pass
    # if test config...
    #     check for and add the test endpoint
    # else...
    #     check if any endpoints available for the chain_id
    found_endpoint = True
    try:
        endpoint = cfg.get_endpoint(chain_id)
    except:
        found_endpoint = False
    
    #     print settings if there are endpoints available
    if found_endpoint:
        choice = input(
            f"This endpoint is available for chain_id {chain_id}: {str(endpoint)}"
            "Do you want to use it? (y/n)"
            )

        if choice.lower() == "y":

            return cfg

        if choice.lower == "n":

            return set_endpoint(cfg, chain_id)

    if not found_endpoint:

        return set_endpoint(cfg, chain_id)


def check_config(cfg: TelliotConfig) -> bool:

    # do they want the current chain id, endpint and account?
    # if yes, proceed to reporting
    # if not, trigger above functions

    try:
        cfg.get_endpoint()
    except:
        return False
    if find_accounts(chain_id=cfg.main.chain_id) is not None:
        return True
    else: 
        return False




def set_endpoint(cfg: TelliotConfig, chain_id:int):

    network_name = input("Enter network name: ")
    provider = input("Enter Provider: ")
    rpc_url = input("Enter RPC url")
    explorer_url = input("Enter Explorer url: ")

    new_endpoint = RPCEndpoint(chain_id, network_name, provider, rpc_url, explorer_url)

    cfg.endpoints.add(new_endpoint)

    click.echo(f"{new_endpoint} added!")

    return cfg


def set_config():
    pass
