import pytest
import pytest_asyncio
from brownie import accounts
from brownie import SampleFlexReporter
from telliot_core.apps.core import ChainedAccount
from telliot_core.apps.core import Contract
from telliot_core.apps.core import find_accounts
from telliot_core.apps.core import TelliotCore
from telliot_core.utils.response import ResponseStatus

from telliot_feeds.datafeed import DataFeed
from telliot_feeds.feeds.eth_usd_feed import eth_usd_median_feed
from telliot_feeds.feeds.matic_usd_feed import matic_usd_median_feed
from telliot_feeds.reporters.tellor_360 import Tellor360Reporter
from telliot_feeds.utils.log import get_logger


logger = get_logger(__name__)

account_fake = accounts.add("023861e2ceee1ea600e43cbd203e9e01ea2ed059ee3326155453a1ed3b1113a9")
try:
    account = find_accounts(name="fake_flex_custom_reporter_address", chain_id=80001)[0]
except IndexError:
    account = ChainedAccount.add(
        name="fake_flex_custom_reporter_address",
        chains=80001,
        key="023861e2ceee1ea600e43cbd203e9e01ea2ed059ee3326155453a1ed3b1113a9",
        password="",
    )


@pytest.fixture(scope="function")
def mock_reporter_contract(tellorflex_360_contract, mock_token_contract, mock_autopay_contract):
    """mock custom reporter contract"""
    return account_fake.deploy(
        SampleFlexReporter,
        tellorflex_360_contract.address,
        mock_autopay_contract.address,
        mock_token_contract.address,
        1,
    )


@pytest_asyncio.fixture(scope="function")
async def custom_reporter(
    mumbai_test_cfg,
    mock_autopay_contract,
    mock_token_contract,
    mock_reporter_contract,
):
    async with TelliotCore(config=mumbai_test_cfg) as core:
        custom_contract = Contract(mock_reporter_contract.address, mock_reporter_contract.abi, core.endpoint, account)
        custom_contract.connect()
        contracts = core.get_tellor360_contracts()
        contracts.oracle.address = custom_contract.address
        contracts.autopay.address = mock_autopay_contract.address
        contracts.autopay.abi = mock_autopay_contract.abi
        contracts.token.address = mock_token_contract.address

        contracts.oracle.connect()
        contracts.token.connect()
        contracts.autopay.connect()

        r = Tellor360Reporter(
            transaction_type=0,
            oracle=contracts.oracle,
            token=contracts.token,
            autopay=contracts.autopay,
            endpoint=core.endpoint,
            account=account,
            chain_id=80001,
            gas_limit=350000,
        )
        # mint token and send to reporter address
        mock_token_contract.mint(account.address, 1000e18)
        mock_token_contract.mint(accounts[0].address, 1000e18)
        mock_token_contract.mint(mock_reporter_contract.address, 100e18)
        mock_token_contract.approve(mock_autopay_contract.address, 10e18)

        mock_autopay_contract.tip(
            "0xd913406746edf7891a09ffb9b26a12553bbf4d25ecf8e530ec359969fe6a7a9c",
            int(10e18),
            "0x00000000000000000000000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000080000000000000000000000000000000000000000000000000000000000000000953706f745072696365000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000c0000000000000000000000000000000000000000000000000000000000000004000000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000003646169000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000037573640000000000000000000000000000000000000000000000000000000000",  # noqa: E501
        )
        # send eth from brownie address to reporter address for txn fees
        accounts[1].transfer(account.address, "1 ether")
        # init governance address
        await contracts.oracle.write(
            "init", _governanceAddress=accounts[0].address, gas_limit=350000, legacy_gas_price=1
        )

        return r


@pytest.mark.asyncio
async def test_YOLO_feed_suggestion(custom_reporter):
    custom_reporter.expected_profit = "YOLO"
    feed = await custom_reporter.fetch_datafeed()

    assert feed is not None
    assert isinstance(feed, DataFeed)


@pytest.mark.asyncio
async def test_ensure_profitable(custom_reporter):
    status = await custom_reporter.ensure_profitable(matic_usd_median_feed)

    assert isinstance(status, ResponseStatus)
    assert status.ok


@pytest.mark.asyncio
async def test_submit_once(custom_reporter):
    _, status = await custom_reporter.report_once()
    assert status.ok


@pytest.mark.asyncio
async def test_ensure_staked(custom_reporter):
    staked, status = await custom_reporter.ensure_staked()

    assert isinstance(status, ResponseStatus)
    assert isinstance(staked, bool)
    if status.ok:
        assert staked
    else:
        assert "Unable to approve staking" in status.error


@pytest.mark.asyncio
async def test_check_reporter_lock(custom_reporter):
    status = await custom_reporter.check_reporter_lock()

    assert isinstance(status, ResponseStatus)
    if not status.ok:
        assert ("reporter lock" in status.error) or ("Staker balance too low" in status.error)


@pytest.mark.asyncio
async def test_get_num_reports_by_id(custom_reporter):
    qid = eth_usd_median_feed.query.query_id
    count, status = await custom_reporter.get_num_reports_by_id(qid)

    assert isinstance(status, ResponseStatus)
    if status.ok:
        assert isinstance(count, int)
    else:
        assert count is None
