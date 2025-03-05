"""Pytest Fixtures used for testing Pytelliot"""
import pytest
import pytest_asyncio
from ape import networks
from chained_accounts import ChainedAccount
from chained_accounts import find_accounts
from hexbytes import HexBytes
from multicall import multicall
from multicall.constants import MULTICALL3_ADDRESSES
from multicall.constants import Network
from telliot_core.apps.core import TelliotCore
from telliot_core.apps.telliot_config import TelliotConfig
from web3 import Web3

from telliot_feeds.datasource import DataSource
from telliot_feeds.dtypes.datapoint import datetime_now_utc
from telliot_feeds.dtypes.datapoint import OptionalDataPoint
from telliot_feeds.reporters.tellor_360 import Tellor360Reporter


NAME = "hardhat"


@pytest.fixture(scope="session")
def local_network_api():
    return networks.ethereum.local


@pytest.fixture(scope="session")
def name():
    return NAME


@pytest.fixture(scope="session")
def connected_provider(name, local_network_api, chain):
    """
    The main HH local-network (non-fork) instance.
    """

    with local_network_api.use_provider(name) as provider:

        yield provider


@pytest.fixture(autouse=True)
def setup(chain):
    snapshot = chain.snapshot()
    yield
    chain.restore(snapshot)


@pytest.fixture(scope="session")
def mumbai_test_key_name():
    return "mumbai_test_key"


@pytest.fixture(autouse=True)
def amoy_test_key_name():
    return "amoy_test_key"


@pytest.fixture
def custom_reporter_name():
    return "custom_reporter_address"


@pytest.fixture
def sepolia_test_key_name():
    return "sepolia_test_key"


class BadDataSource(DataSource[float]):
    """Source that does not return an updated DataPoint."""

    async def fetch_new_datapoint(self) -> OptionalDataPoint[float]:
        return None, None


@pytest.fixture(scope="module")
def bad_datasource():
    """Used for testing no updated value for datafeeds."""

    return BadDataSource()


class GoodFakeSource(DataSource[float]):
    """Source that does not return an updated DataPoint."""

    async def fetch_new_datapoint(self) -> OptionalDataPoint[float]:
        datapoint = (1234.0, datetime_now_utc())
        self.store_datapoint(datapoint)
        return datapoint


@pytest.fixture(autouse=True)
def guaranteed_price_source():
    """Used for testing no updated value for datafeeds."""
    return GoodFakeSource()


@pytest.fixture(autouse=True)
def sender(accounts, mumbai_test_key_name):
    accts = find_accounts(chain_id=80001, name=mumbai_test_key_name)

    for acct in accts:
        if acct.name == mumbai_test_key_name:
            acct.delete()
            break
    acct = ChainedAccount.add(
        mumbai_test_key_name,
        chains=80001,
        key=accounts[0].private_key,
        password="",
    )

    return accounts[0]


@pytest.fixture(autouse=True)
def amoy_test_key(accounts, amoy_test_key_name):
    accts = find_accounts(chain_id=80002, name=amoy_test_key_name)

    for acct in accts:
        if acct.name == amoy_test_key_name:
            acct.delete()
            break
    acct = ChainedAccount.add(
        amoy_test_key_name,
        chains=80002,
        key=accounts[0].private_key,
        password="",
    )

    return accounts[0]


@pytest.fixture(autouse=True)
def sepolia_test_key(accounts, sepolia_test_key_name):
    accts = find_accounts(chain_id=11155111, name=sepolia_test_key_name)

    for acct in accts:
        if acct.name == sepolia_test_key_name:
            acct.delete()
            break
    acct = ChainedAccount.add(
        sepolia_test_key_name,
        chains=11155111,
        key=accounts[0].private_key,
        password="",
    )
    return accounts[0]


@pytest.fixture(scope="function")
def custom_reporter_chained_account(accounts, custom_reporter_name):
    accts = find_accounts(chain_id=80001, name=custom_reporter_name)
    for acct in accts:
        if acct.name == custom_reporter_name:
            acct.delete()
            break
    acct = ChainedAccount.add(
        custom_reporter_name,
        chains=80001,
        key=accounts[2].private_key,
        password="",
    )
    return acct


@pytest.fixture(scope="function")
def custom_reporter_ape_account(accounts):
    return accounts[2]


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

    return cfg


@pytest.fixture(scope="session")
def deploy_contracts(project, accounts):
    token = accounts[0].deploy(project.TellorPlayground)
    flex = accounts[0].deploy(
        project.TellorFlex,
        token.address,
        43200,  # 12 hours reporting lock
        Web3.to_wei(100, "ether"),  # $100 stake amount dollar target
        Web3.to_wei(15, "ether"),  # $15 staking token current price
        Web3.to_wei(10, "ether"),  # 10 TRB minimum stake amount
        HexBytes(
            "0x5c13cd9c97dbb98f2429c101a2a8150e6c7a0ddaff6124ee176a3a411067ded0"
        ),  # TRB/USD staking token price query id
    )

    gov = accounts[0].deploy(project.Governance, flex.address, token.address)
    flex.init(gov.address, sender=accounts[0])
    query_data_storage_contract = accounts[0].deploy(project.QueryDataStorage)
    autopay = accounts[0].deploy(
        project.Autopay,
        flex.address,
        query_data_storage_contract.address,
        20,
    )

    return token, flex, gov, query_data_storage_contract, autopay


@pytest.fixture(scope="session")
def multicall_contract(project, accounts):
    mc = accounts[0].deploy(project.Multicall3)
    MULTICALL3_ADDRESSES[Network.Mumbai] = mc.address
    multicall.state_override_supported = lambda _: False


@pytest.fixture(scope="session")
def mumbai_test_cfg(connected_provider):
    return local_node_cfg(chain_id=80001)


@pytest.fixture(scope="session")
def amoy_test_cfg(connected_provider):
    return local_node_cfg(chain_id=80002)


@pytest.fixture
def random_key_no_funds(accounts):
    accts = find_accounts(chain_id=80001, name="random_key_no_funds")

    for acct in accts:
        if acct.name == "random_key_no_funds":
            acct.delete()
            break
    acct = ChainedAccount.add(
        "random_key_no_funds",
        chains=80001,
        key="91e607f51e79a3d4cb45126c67a539abf9e34461ac95320d666b009762cd392b",
        password="",
    )
    return acct


@pytest_asyncio.fixture(scope="function")
async def tellor_360(project, accounts, mumbai_test_cfg, deploy_contracts, chain, mumbai_test_key_name):
    token, oracle, _, _, autopay = deploy_contracts
    flexabi = project.TellorFlex.contract_type.model_dump().get("abi", [])
    autopayabi = project.Autopay.contract_type.model_dump().get("abi", [])
    async with TelliotCore(config=mumbai_test_cfg, account_name=mumbai_test_key_name) as core:
        account = core.get_account()

        tellor360 = core.get_tellor360_contracts()
        tellor360.oracle.address = oracle.address
        tellor360.oracle.abi = flexabi
        tellor360.autopay.address = autopay.address
        tellor360.autopay.abi = autopayabi
        tellor360.token.address = token.address

        tellor360.oracle.connect()
        tellor360.token.connect()
        tellor360.autopay.connect()

        # mint token and send to reporter address
        token.faucet(account.address, sender=accounts[0])

        # approve token to be spent by autopay contract
        token.approve(autopay.address, 10000000000000, sender=accounts[0])

        # send eth from ape address to reporter address for txn fees
        accounts[1].transfer(account.address, "1 ether")

        return tellor360, account


@pytest_asyncio.fixture(scope="function")
async def tellor_flex_reporter(accounts, mumbai_test_cfg, deploy_contracts, mumbai_test_key_name):
    async with TelliotCore(config=mumbai_test_cfg, account_name=mumbai_test_key_name) as core:
        mock_token_contract, mock_flex_contract, _, _, mock_autopay_contract = deploy_contracts
        account = core.get_account()

        flex = core.get_tellor360_contracts()
        flex.oracle.address = mock_flex_contract.address
        flex.autopay.address = mock_autopay_contract.address
        flex.token.address = mock_token_contract.address

        flex.oracle.connect()
        flex.token.connect()
        flex.autopay.connect()
        flex = core.get_tellor360_contracts()

        r = Tellor360Reporter(
            oracle=flex.oracle,
            token=flex.token,
            autopay=flex.autopay,
            endpoint=core.endpoint,
            account=account,
            chain_id=80001,
            transaction_type=0,
            min_native_token_balance=0,
        )
        # mint token and send to reporter address
        mock_token_contract.faucet(account.address, sender=accounts[0])

        # send eth from ape address to reporter address for txn fees
        accounts[1].transfer(account.address, "1 ether")

        return r


@pytest.fixture
def mock_price_feed():
    """
    Fixture to mock price feeds with configurable values, handling varying numbers of sources.
    """
    original_methods = []

    def _setup_mock(feed, mock_values, sources=None, timestamp=None):
        if timestamp is None:
            timestamp = datetime_now_utc()

        if sources is None:
            sources = feed.source.sources

        source_count = len(sources)
        final_values = []

        final_values = mock_values[:source_count]

        for source in sources:
            original_methods.append((source, source.fetch_new_datapoint))

        for i, source in enumerate(sources):
            price = final_values[i]

            async def mock_fetch(self=source, price=price, ts=timestamp):
                datapoint = (price, ts)
                if hasattr(self, "store_datapoint"):
                    self.store_datapoint(datapoint)
                return datapoint

            source.fetch_new_datapoint = mock_fetch

    yield _setup_mock

    # Restore original methods after test completes
    for source, original_method in original_methods:
        source.fetch_new_datapoint = original_method
