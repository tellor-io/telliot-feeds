import pytest
import pytest_asyncio
from brownie import accounts
from telliot_core.apps.core import TelliotCore
from telliot_core.utils.response import ResponseStatus

from telliot_feeds.datafeed import DataFeed
from telliot_feeds.feeds.eth_usd_feed import eth_usd_median_feed
from telliot_feeds.feeds.matic_usd_feed import matic_usd_median_feed
from telliot_feeds.reporters.tellorflex import TellorFlexReporter


@pytest_asyncio.fixture(scope="function")
async def polygon_reporter(
    mumbai_test_cfg, mock_flex_contract, mock_autopay_contract, mock_token_contract, multicall_contract
):
    async with TelliotCore(config=mumbai_test_cfg) as core:

        account = core.get_account()

        flex = core.get_tellorflex_contracts()
        flex.oracle.address = mock_flex_contract.address
        flex.autopay.address = mock_autopay_contract.address
        flex.token.address = mock_token_contract.address

        flex.oracle.connect()
        flex.token.connect()
        flex.autopay.connect()
        flex = core.get_tellorflex_contracts()

        r = TellorFlexReporter(
            oracle=flex.oracle,
            token=flex.token,
            autopay=flex.autopay,
            endpoint=core.endpoint,
            account=account,
            chain_id=80001,
        )
        # mint token and send to reporter address
        mock_token_contract.mint(account.address, 1000e18)

        # send eth from brownie address to reporter address for txn fees
        accounts[1].transfer(account.address, "1 ether")

        return r


@pytest.mark.asyncio
async def test_YOLO_feed_suggestion(polygon_reporter):
    polygon_reporter.expected_profit = "YOLO"
    feed = await polygon_reporter.fetch_datafeed()

    assert feed is not None
    assert isinstance(feed, DataFeed)


@pytest.mark.asyncio
async def test_ensure_profitable(polygon_reporter):
    status = await polygon_reporter.ensure_profitable(matic_usd_median_feed)

    assert isinstance(status, ResponseStatus)
    assert status.ok


@pytest.mark.asyncio
async def test_fetch_gas_price(polygon_reporter):
    price = await polygon_reporter.fetch_gas_price()

    assert isinstance(price, int)
    assert price > 0


@pytest.mark.asyncio
async def test_ensure_staked(polygon_reporter):
    staked, status = await polygon_reporter.ensure_staked()

    assert isinstance(status, ResponseStatus)
    assert isinstance(staked, bool)
    if status.ok:
        assert staked
    else:
        assert "Unable to approve staking" in status.error


@pytest.mark.asyncio
async def test_check_reporter_lock(polygon_reporter):
    status = await polygon_reporter.check_reporter_lock()

    assert isinstance(status, ResponseStatus)
    if not status.ok:
        assert ("reporter lock" in status.error) or ("Staker balance too low" in status.error)


@pytest.mark.asyncio
async def test_get_num_reports_by_id(polygon_reporter):
    qid = eth_usd_median_feed.query.query_id
    count, status = await polygon_reporter.get_num_reports_by_id(qid)

    assert isinstance(status, ResponseStatus)
    if status.ok:
        assert isinstance(count, int)
    else:
        assert count is None


@pytest.mark.asyncio
async def test_fetch_gas_price_error(polygon_reporter, caplog):
    # Test invalid gas price speed
    r = polygon_reporter
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
