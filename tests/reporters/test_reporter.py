from unittest.mock import Mock
from unittest.mock import patch

import pytest
from telliot_core.utils.response import ResponseStatus
from web3.contract import Contract

from telliot_feeds.feeds import matic_usd_median_feed
from telliot_feeds.feeds import trb_usd_median_feed
from telliot_feeds.reporters.tellor_360 import Tellor360Reporter
from telliot_feeds.reporters.types import StakerInfo


@pytest.mark.asyncio
async def test_get_stake_amount(tellor_flex_reporter):
    r: Tellor360Reporter = tellor_flex_reporter
    stake_amount, status = await r.get_stake_amount()
    assert stake_amount > 0
    assert isinstance(stake_amount, int)
    assert status.ok

    type(r.oracle.contract).get_function_by_name = Mock(side_effect=Exception("Mocked exception"))
    stake_amount, status = await r.get_stake_amount()
    assert stake_amount is None
    assert not status.ok
    assert status.error == (
        "Unable to read current stake amount: error reading from contract: Exception('Mocked exception')"
    )


@pytest.mark.asyncio
async def test_get_staker_details(tellor_flex_reporter):
    r: Tellor360Reporter = tellor_flex_reporter
    staker_details, status = await r.get_staker_details()
    # staker details before any staking/reporting
    assert isinstance(staker_details, StakerInfo)
    assert staker_details.start_date == 0
    assert status.ok

    type(r.oracle.contract).get_function_by_name = Mock(side_effect=Exception("Mocked exception"))
    staker_details, status = await r.get_staker_details()
    assert staker_details is None
    assert not status.ok
    assert status.error == (
        "Unable to read account staker info: error reading from contract: Exception('Mocked exception')"
    )


@pytest.mark.asyncio
async def test_get_current_token_balance(tellor_flex_reporter):
    r: Tellor360Reporter = tellor_flex_reporter
    token_balance, status = await r.get_current_token_balance()
    assert token_balance > 0
    assert isinstance(token_balance, int)
    assert status.ok

    type(r.token.contract).get_function_by_name = Mock(side_effect=Exception("Mocked exception"))
    token_balance, status = await r.get_current_token_balance()
    assert token_balance is None
    assert not status.ok
    assert status.error == (
        "Unable to read account balance: error reading from contract: Exception('Mocked exception')"
    )


@pytest.mark.asyncio
async def test_ensure_staked(tellor_flex_reporter):
    """Test ensure_staked method."""
    r: Tellor360Reporter = tellor_flex_reporter
    # staker balance should initiate with None
    assert r.stake_info.current_staker_balance is None
    # ensure stake method fetches stake amount and staker details
    # and stakes reporter if not already staked or has a low stake
    known_stake, status = await r.ensure_staked()
    # check that reporter got staked
    assert r.stake_info.current_staker_balance > 0
    assert status.ok
    assert known_stake
    # mock the oracle read call to raise an exception
    with patch.object(Contract, "get_function_by_name", side_effect=Exception("Mocked exception")):
        known_stake, status = await r.ensure_staked()
        assert not status.ok
        assert not known_stake


@pytest.mark.asyncio
async def test_check_stake_amount_change(tellor_flex_reporter):
    """Test what happens when the stake amount changes during reporting loops."""
    r: Tellor360Reporter = tellor_flex_reporter
    # check stake amount
    stake_amount, status = await r.get_stake_amount()
    assert stake_amount > 0
    # check staker details
    check1, status = await r.get_staker_details()
    assert status.ok
    assert check1.stake_balance == 0
    # stake by calling ensure_staked method which automatically stakes reporter
    # if staked balance is lower than stake amount
    known_stake, status = await r.ensure_staked()
    assert known_stake
    assert status.ok
    # check staker details again
    check2, status = await r.get_staker_details()
    assert status.ok
    assert check2.stake_balance > check1.stake_balance
    # check staker details again after calling ensure_staked, should be same as check2
    known_stake, status = await r.ensure_staked()
    assert known_stake
    assert status.ok
    check3, status = await r.get_staker_details()
    assert status.ok
    assert check3.stake_balance == check2.stake_balance
    # mock increasing stake amount
    with patch.object(Tellor360Reporter, "get_stake_amount", return_value=(stake_amount + 1, ResponseStatus())):
        known_stake, status = await r.ensure_staked()
        assert known_stake
        assert status.ok
        check4, status = await r.get_staker_details()
        assert status.ok
        # reporter staked balance should be increased by 1
        assert check4.stake_balance == check3.stake_balance + 1
        # mock additional stake chosen by user
        assert r.stake == 0
        r.stake = stake_amount + 2
        known_stake, status = await r.ensure_staked()
        assert known_stake
        assert status.ok
        b, status = await r.get_staker_details()
        assert status.ok
        # reporter staked balance should be increased by 2
        assert b.stake_balance == check3.stake_balance + 2


@pytest.mark.asyncio
async def test_staking_after_a_reporter_slashing(tellor_flex_reporter, caplog):
    """Test when reporter is disputed that they automatically be staked again"""
    r: Tellor360Reporter = tellor_flex_reporter
    # ensure reporter is staked
    known_stake, status = await r.ensure_staked()
    assert known_stake
    assert status.ok
    # mock reporter being slashed
    with patch.object(
        Tellor360Reporter,
        "get_staker_details",
        return_value=(StakerInfo(0, 0, 0, 0, 0, 0, 0, 0, True), ResponseStatus()),
    ):
        trb_balance, status = await r.get_current_token_balance()
        known_stake, status = await r.ensure_staked()
        assert known_stake
        assert status.ok
        assert "Your staked balance has decreased, account might be in dispute" in caplog.text
        trb_balance2, status = await r.get_current_token_balance()
        assert trb_balance2 < trb_balance


@pytest.mark.asyncio
async def test_stake_info(tellor_flex_reporter, guaranteed_price_source, chain):
    """Test stake info changes and status"""
    r: Tellor360Reporter = tellor_flex_reporter
    feed = matic_usd_median_feed
    feed.source = guaranteed_price_source
    trb_usd_median_feed.source = guaranteed_price_source
    r.expected_profit = "YOLO"
    r.datafeed = feed
    with patch.object(Tellor360Reporter, "check_reporter_lock", return_value=ResponseStatus()):
        assert r.stake_info.last_report == 0
        assert r.stake_info.reports_count == 0
        assert not r.stake_info.is_in_dispute()
        assert r.stake_info.last_report_time == 0
        assert r.stake_info.last_report_time == 0
        assert len(r.stake_info.stake_amount_history) == 0
        assert len(r.stake_info.staker_balance_history) == 0
        # report and check info
        await r.report_once()
        assert len(r.stake_info.stake_amount_history) == 1
        # this should be of length 2 since its updated after staking
        assert len(r.stake_info.staker_balance_history) == 2
        # bypass 12 hour reporting lock
        chain.sleep(84600)
        r.datafeed = feed
        await r.report_once()
        # last report time should update during the second reporting loop
        assert r.stake_info.last_report_time > 0
        # reports count should be 1 during the second reporting loop
        assert r.stake_info.reports_count == 1
        # should be of length always since thats the max datapoints
        assert len(r.stake_info.stake_amount_history) == 2
        assert len(r.stake_info.staker_balance_history) == 2

        await r.report_once()
        # reports count should be 2 during the third reporting loop
        assert r.stake_info.reports_count == 2
        assert len(r.stake_info.stake_amount_history) == 2
        assert len(r.stake_info.staker_balance_history) == 2
        # mock a dispute by inputing a bad value to staker balance history deque
        r.stake_info.staker_balance_history.append(0)
        # dispute should be detected and return True
        assert r.stake_info.is_in_dispute()
