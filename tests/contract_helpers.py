import pytest

from brownie import StakingToken, TellorFlex, accounts, chain
from web3 import Web3


def test_connect_local_web3():
    # w3 = Web3(Web3.WebsocketProvider('wss://127.0.0.1:8545'))
    w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:8545'))
    chain.mine(10)
    block = w3.eth.get_block('latest')

    # assert w3.isConnected()
    assert block.number == 10


@pytest.fixture
def trb(): # Tellor Tributes (TRB)
    return accounts[0].deploy(StakingToken)


@pytest.fixture
def tellor_flex(trb):
    return accounts[0].deploy(TellorFlex, trb.address)


def test_mint_test_token(trb):
    trb.mint(accounts[0], 1000, {'from': accounts[0]})

    assert trb.balanceOf(accounts[0]) == 1000


# def test_approve(trb):
#     trb.approve(accounts[1], 100, {'from': accounts[0]})
#     assert trb.allowance(accounts[0], accounts[1]) == 100
