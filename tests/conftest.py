"""Pytest Fixtures used for testing Pytelliot"""
import os

import pytest
from brownie import chain
from chained_accounts import ChainedAccount
from chained_accounts import find_accounts
from telliot_core.apps.telliot_config import TelliotConfig
from telliot_core.datasource import DataSource
from telliot_core.dtypes.datapoint import datetime_now_utc
from telliot_core.dtypes.datapoint import OptionalDataPoint

from telliot_feed_examples.utils.cfg import mainnet_config


@pytest.fixture(scope="session", autouse=True)
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
            ChainedAccount.add(
                "git-rinkeby-key", chains=4, key=os.environ["PRIVATE_KEY"], password=""
            )
        else:
            raise Exception("Need a rinkeby account")

    return cfg


@pytest.fixture(scope="session", autouse=True)
def mainnet_test_cfg():
    """Get mainnet endpoint from config

    If environment variables are defined, they will override the values in config files
    """
    return mainnet_config()


@pytest.fixture(scope="session", autouse=True)
def mumbai_cfg():
    """Return a test telliot configuration for use on polygon-mumbai

    If environment variables are defined, they will override the values in config files
    """
    cfg = TelliotConfig()

    # Override configuration for rinkeby testnet
    cfg.main.chain_id = 80001

    endpt = cfg.get_endpoint()
    if "INFURA_API_KEY" in endpt.url:
        endpt.url = (
            f'https://polygon-mumbai.infura.io/v3/{os.environ["INFURA_API_KEY"]}'
        )

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


@pytest.fixture(scope="session", autouse=True)
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
            ChainedAccount.add(
                "git-ropsten-key", chains=3, key=os.environ["PRIVATE_KEY"], password=""
            )
        else:
            raise Exception("Need a ropsten account")

    return cfg


@pytest.fixture(scope="session")
def bad_source():
    """Used for testing no updated value for datafeeds."""

    class BadSource(DataSource[float]):
        """Source that does not return an updated DataPoint."""

        async def fetch_new_datapoint(self) -> OptionalDataPoint[float]:
            return None, None

    return BadSource()


@pytest.fixture(scope="session")
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
def mumbai_test_cfg(scope="session", autouse=True):
    return local_node_cfg(chain_id=80001)
