"""Pytest Fixtures used for testing Pytelliot"""
import asyncio
import os

import pytest
from brownie import accounts
from brownie import Autopay
from brownie import chain
from brownie import multicall as brownie_multicall
from brownie import StakingToken
from brownie import TellorFlex
from brownie import TellorXMasterMock
from brownie import TellorXOracleMock
from chained_accounts import ChainedAccount
from chained_accounts import find_accounts
from multicall import multicall
from multicall.constants import MULTICALL2_ADDRESSES
from multicall.constants import MULTICALL_ADDRESSES
from multicall.constants import Network
from telliot_core.apps.telliot_config import TelliotConfig

from telliot_feeds.datasource import DataSource
from telliot_feeds.dtypes.datapoint import datetime_now_utc
from telliot_feeds.dtypes.datapoint import OptionalDataPoint
from telliot_feeds.utils.cfg import mainnet_config


@pytest.fixture(scope="module", autouse=True)
def shared_setup(module_isolation):
    pass


@pytest.fixture(scope="module", autouse=True)
def event_loop():
    return asyncio.get_event_loop()


@pytest.fixture(scope="module", autouse=True)
def rinkeby_cfg():
    """Get rinkeby endpoint from config

    If environment variables are defined, they will override the values in config files
    """
    cfg = TelliotConfig()

    # Override configuration for rinkeby testnet
    cfg.main.chain_id = 4

    rinkeby_endpoint = cfg.get_endpoint()
    # assert rinkeby_endpoint.network == "rinkeby"

    if os.getenv("NODE_URL", None):
        rinkeby_endpoint.url = os.environ["NODE_URL"]

    rinkeby_accounts = find_accounts(chain_id=4)
    if not rinkeby_accounts:
        # Create a test account using PRIVATE_KEY defined on github.
        key = os.getenv("PRIVATE_KEY", None)
        if key:
            ChainedAccount.add("git-rinkeby-key", chains=4, key=os.environ["PRIVATE_KEY"], password="")
        else:
            raise Exception("Need a rinkeby account")

    return cfg


@pytest.fixture(scope="module", autouse=True)
def mainnet_test_cfg():
    """Get mainnet endpoint from config

    If environment variables are defined, they will override the values in config files
    """
    return mainnet_config()


@pytest.fixture(scope="module", autouse=True)
def mumbai_cfg():
    """Return a test telliot configuration for use on polygon-mumbai

    If environment variables are defined, they will override the values in config files
    """
    cfg = TelliotConfig()

    # Override configuration for rinkeby testnet
    cfg.main.chain_id = 80001

    endpt = cfg.get_endpoint()
    if "INFURA_API_KEY" in endpt.url:
        endpt.url = f'https://polygon-mumbai.infura.io/v3/{os.environ["INFURA_API_KEY"]}'

    mumbai_accounts = find_accounts(chain_id=80001)
    if not mumbai_accounts:
        # Create a test account using PRIVATE_KEY defined on github.
        key = os.getenv("PRIVATE_KEY", None)
        if key:
            ChainedAccount.add(
                "git-mumbai-key",
                chains=80001,
                key=os.environ["PRIVATE_KEY"],
                password="",
            )
        else:
            raise Exception("Need a mumbai account")

    return cfg


@pytest.fixture(scope="module", autouse=True)
def ropsten_cfg():
    """Return a test telliot configuration for use on polygon-mumbai

    If environment variables are defined, they will override the values in config files
    """
    cfg = TelliotConfig()

    # Override configuration for ropsten testnet
    cfg.main.chain_id = 3

    endpt = cfg.get_endpoint()
    if "INFURA_API_KEY" in endpt.url:
        endpt.url = f'wss://ropsten.infura.io/ws/v3/{os.environ["INFURA_API_KEY"]}'

    accounts = find_accounts(chain_id=3)
    if not accounts:
        # Create a test account using PRIVATE_KEY defined on github.
        key = os.getenv("PRIVATE_KEY", None)
        if key:
            ChainedAccount.add("git-ropsten-key", chains=3, key=os.environ["PRIVATE_KEY"], password="")
        else:
            raise Exception("Need a ropsten account")

    return cfg


class BadDataSource(DataSource[float]):
    """Source that does not return an updated DataPoint."""

    async def fetch_new_datapoint(self) -> OptionalDataPoint[float]:
        return None, None


@pytest.fixture(scope="module")
def bad_datasource():
    """Used for testing no updated value for datafeeds."""

    return BadDataSource()


@pytest.fixture(scope="module")
def guaranteed_price_source():
    """Used for testing no updated value for datafeeds."""

    class GoodSource(DataSource[float]):
        """Source that does not return an updated DataPoint."""

        async def fetch_new_datapoint(self) -> OptionalDataPoint[float]:
            return (1234.0, datetime_now_utc())

    return GoodSource()


def local_node_cfg(chain_id: int):
    """Return a test telliot configuration for use of tellorFlex contracts. Overrides
    the default Web3 provider with a local Ganache endpoint.
    """

    cfg = TelliotConfig()

    # Use a chain_id with TellorFlex contracts deployed
    cfg.main.chain_id = chain_id

    endpt = cfg.get_endpoint()

    # Configure testing using local Ganache node
    endpt.url = "http://127.0.0.1:8545"

    # Advance block number to avoid assertion error in endpoint.connect():
    # connected = self._web3.eth.get_block_number() > 1
    chain.mine(10)

    accounts = find_accounts(chain_id=chain_id)
    if not accounts:
        # Create a test account using PRIVATE_KEY defined on github.
        key = os.getenv("PRIVATE_KEY", None)
        if key:
            ChainedAccount.add(
                "git-tellorflex-test-key",
                chains=chain_id,
                key=os.environ["PRIVATE_KEY"],
                password="",
            )
        else:
            raise Exception(f"Need an account for {chain_id}")

    return cfg


@pytest.fixture
def mumbai_test_cfg(scope="function", autouse=True):
    return local_node_cfg(chain_id=80001)


@pytest.fixture
def rinkeby_test_cfg(scope="function", autouse=True):
    return local_node_cfg(chain_id=4)


@pytest.fixture
def ropsten_test_cfg(scope="function", autouse=True):
    return local_node_cfg(chain_id=3)


@pytest.fixture(scope="module", autouse=True)
def mock_token_contract():
    """mock token to use for staking"""
    return accounts[0].deploy(StakingToken)


@pytest.fixture(scope="module", autouse=True)
def mock_flex_contract(mock_token_contract):
    """mock oracle(TellorFlex) contract to stake in"""
    return accounts[0].deploy(TellorFlex, mock_token_contract.address, accounts[0], 10e18, 60)


@pytest.fixture(scope="module", autouse=True)
def mock_autopay_contract(mock_flex_contract, mock_token_contract):
    """mock payments(Autopay) contract for tipping and claiming tips"""
    return accounts[0].deploy(
        Autopay,
        mock_flex_contract.address,
        mock_token_contract.address,
        accounts[0],
        20,
    )


@pytest.fixture
def tellorx_oracle_mock_contract():
    return accounts[0].deploy(TellorXOracleMock)


@pytest.fixture
def tellorx_master_mock_contract():
    return accounts[0].deploy(TellorXMasterMock)


@pytest.fixture
def multicall_contract():
    #  deploy multicall contract to brownie chain and add chain id to multicall module
    addy = brownie_multicall.deploy({"from": accounts[0]})
    Network.Brownie = 1337
    # add multicall contract address to multicall module
    MULTICALL_ADDRESSES[Network.Brownie] = MULTICALL2_ADDRESSES[Network.Brownie] = addy.address
    multicall.state_override_supported = lambda _: False
