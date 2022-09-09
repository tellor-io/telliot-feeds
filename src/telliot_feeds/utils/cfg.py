from typing import Optional

import click

from chained_accounts import ChainedAccount
from chained_accounts import find_accounts
from telliot_core.apps.telliot_config import TelliotConfig


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

    #check if configs are setup
    #prompt the user to select a differnt chain id
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


def setup_endpoint(cfg:TelliotConfig, chain_id:int):
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


def check_config(cfg: TelliotConfig):

    #do they want the current chain id, endpint and account?
    # if yes, proceed to reporting
    # if not, trigger above functions

    # print current settings of cfg, does the user want to replace any?
    click.echo(f"Your current config settings on chain_id {cfg.main.chain_id}: " + str(cfg.main))
    # replace the ones the user wants to replace
