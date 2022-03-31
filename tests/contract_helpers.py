import secrets

import pytest
from brownie import accounts
from brownie import chain
from brownie import StakingToken
from brownie import TellorFlex
from chained_accounts import ChainedAccount
from chained_accounts import find_accounts
from telliot_core.apps.telliot_config import TelliotConfig
from web3 import Web3

# from eth_utils import to_checksum_address


@pytest.fixture(scope="session", autouse=True)
def local_cfg():
    """Use local Ganache endpoint as web3 provider."""
    cfg = TelliotConfig()

    # Use Polygon mumbai testnet chain id, since this will trigger TelliotConfig
    # to use TellorFlex contracts.
    cfg.main.chain_id = 80001

    # Override endpoint with localhost and default Ganache port
    default_endpoint = cfg.get_endpoint()
    default_endpoint.url = "http://127.0.0.1:8545"

    # Create fake test account
    pk = secrets.token_hex(32)
    accounts.add(pk)
    chained_accts = find_accounts(name="_test_account")
    print(dir(ChainedAccount))
    if (
        not chained_accts
        or chained_accts[0].address != "0x3d79f9a83c8bfc5887741a771609da1ac3101f5a"
    ):
        ChainedAccount.add("_test_account", chains=80001, key=pk, password="")

    # Verify correct test account used
    # test_acct = find_accounts(name="_test_account")[0]
    # assert to_checksum_address(test_acct.address) == accounts[-1].address

    # endpoint = cfg.get_endpoint()
    # print("url:", endpoint.url)
    # chain.mine(10)
    # block = endpoint._web3.eth.get_block("latest")
    # assert block.number == 10

    return cfg


# if not test_acct.is_unlocked:
#             test_acct.unlock("")


def test_connect_local_web3(local_cfg):
    # w3 = Web3(Web3.WebsocketProvider('wss://127.0.0.1:8545'))
    w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
    # endpoint = local_cfg.get_endpoint()
    chain.mine(10)
    # block = endpoint._web3.eth.get_block('latest')
    block = w3.eth.get_block("latest")

    # assert w3.isConnected()
    assert block.number == 10
    pass


@pytest.fixture
def trb():  # Tellor Tributes (TRB)
    return accounts[0].deploy(StakingToken)


@pytest.fixture
def tellor_flex(trb):
    return accounts[0].deploy(TellorFlex, trb.address)


def test_mint_test_token(trb):
    trb.mint(accounts[0], 1000, {"from": accounts[0]})

    assert trb.balanceOf(accounts[0]) == 1000


# def test_approve(trb):
#     trb.approve(accounts[1], 100, {'from': accounts[0]})
#     assert trb.allowance(accounts[0], accounts[1]) == 100
