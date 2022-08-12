import pytest
import pytest_asyncio
from brownie import accounts
from brownie import SampleFlexReporter
from telliot_core.apps.core import Contract
from telliot_core.apps.core import TelliotCore
from telliot_core.utils.response import ResponseStatus

from telliot_feeds.datafeed import DataFeed
from telliot_feeds.feeds.eth_usd_feed import eth_usd_median_feed
from telliot_feeds.feeds.matic_usd_feed import matic_usd_median_feed
from telliot_feeds.reporters.custom_flex_reporter import CustomFlexReporter
from telliot_feeds.utils.log import get_logger


logger = get_logger(__name__)

account_fake = accounts.add("0xb80e6a326098e63a16e66504eb994fbbe54000d3f54f3885fabe1eb01fac6cd6")


@pytest.fixture(scope="module", autouse=True)
def mock_reporter_contract(mock_flex_contract, mock_token_contract, mock_autopay_contract):
    """mock custom reporter contract"""
    return account_fake.deploy(
        SampleFlexReporter,
        mock_flex_contract.address,
        mock_autopay_contract.address,
        mock_token_contract.address,
        0,
    )


@pytest_asyncio.fixture(scope="function")
async def custom_reporter(
    mumbai_test_cfg,
    mock_flex_contract,
    mock_autopay_contract,
    mock_token_contract,
    multicall_contract,
    mock_reporter_contract,
):
    async with TelliotCore(config=mumbai_test_cfg) as core:
        account = core.get_account()
        custom_contract = Contract(mock_reporter_contract.address, mock_reporter_contract.abi, core.endpoint, account)
        custom_contract.connect()
        flex = core.get_tellorflex_contracts()
        flex.oracle.address = mock_flex_contract.address
        flex.autopay.address = mock_autopay_contract.address
        flex.token.address = mock_token_contract.address

        flex.oracle.connect()
        flex.token.connect()
        flex.autopay.connect()
        flex = core.get_tellorflex_contracts()

        r = CustomFlexReporter(
            transaction_type=0,
            custom_contract=custom_contract,
            oracle=flex.oracle,
            token=flex.token,
            autopay=flex.autopay,
            endpoint=core.endpoint,
            account=account,
            chain_id=80001,
        )
        # mint token and send to reporter address
        mock_token_contract.mint(account.address, 1000e18)
        mock_token_contract.mint(accounts[0].address, 1000e18)
        mock_token_contract.mint(mock_reporter_contract.address, 100e18)
        mock_token_contract.approve(mock_autopay_contract.address, 10e18)

        mock_autopay_contract.tip(
            "0x000000000000000000000000000000000000000000000000000000000000003b",
            int(10e18),
            "0x00000000000000000000000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000080000000000000000000000000000000000000000000000000000000000000000d4c656761637952657175657374000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000003b",  # noqa: E501
        )
        # send eth from brownie address to reporter address for txn fees
        accounts[1].transfer(account.address, "1 ether")
        accounts[1].transfer()

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
    r = custom_reporter
    receipt, status = await r.report_once()
    if status.ok:
        assert receipt["status"] == 1


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


@pytest.mark.asyncio
async def test_fetch_gas_price_error(custom_reporter, caplog):
    # Test invalid gas price speed
    r = custom_reporter
    gp = await r.fetch_gas_price("blah")
    assert gp is None
    assert "Invalid gas price speed for matic gasstation: blah" in caplog.text

    # Test fetch gas price failure
    async def _fetch_gas_price():
        return None

    r.fetch_gas_price = lambda: _fetch_gas_price()
    r.stake = 1e100
    staked, status = await r.ensure_staked()
    assert not staked
    assert not status.ok
    assert "Unable to fetch matic gas price for staking" in status.error
