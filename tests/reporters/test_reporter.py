from unittest.mock import Mock

import pytest

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
    r: Tellor360Reporter = tellor_flex_reporter
    staked, status = await r.ensure_staked()
    type(r.oracle.contract).get_function_by_name = Mock(side_effect=Exception("Mocked exception"))
    staked, status = await r.ensure_staked()
    assert not status.ok
    assert not staked
    print(status.error)
