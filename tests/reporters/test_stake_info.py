from telliot_feeds.utils.stake_info import StakeInfo

stake_info = StakeInfo()


def test_storage_length():
    assert len(stake_info.stake_amount_history) == 0
    # Add some stake amounts
    stake_info.store_stake_amount(100)
    assert len(stake_info.stake_amount_history) == 1
    stake_info.store_stake_amount(200)
    assert len(stake_info.stake_amount_history) == 2
    stake_info.store_stake_amount(300)  # This should cause 100 to be removed
    assert len(stake_info.stake_amount_history) == 2
    assert stake_info.stake_amount_history[0] == 200
    assert stake_info.stake_amount_history[1] == 300
