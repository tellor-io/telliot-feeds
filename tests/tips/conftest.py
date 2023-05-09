import pytest
from brownie import accounts
from brownie import Autopay
from telliot_core.apps.core import TelliotCore
from telliot_core.utils.timestamp import TimeStamp

from telliot_feeds.reporters.tips import CATALOG_QUERY_DATA
from telliot_feeds.reporters.tips import CATALOG_QUERY_IDS


txn_kwargs = {"gas_limit": 3500000, "legacy_gas_price": 1}


@pytest.fixture(scope="function")
async def autopay_contract_setup(mumbai_test_cfg, mock_flex_contract, mock_token_contract, query_data_storage_contract):
    autopay_contract = accounts[0].deploy(
        Autopay,
        mock_flex_contract.address,
        query_data_storage_contract.address,
        20,
    )
    async with TelliotCore(config=mumbai_test_cfg) as core:

        # get PubKey and PrivKey from config files
        account = core.get_account()

        flex = core.get_tellor360_contracts()
        flex.oracle.address = mock_flex_contract.address
        flex.oracle.abi = mock_flex_contract.abi
        flex.autopay.address = autopay_contract.address
        flex.autopay.abi = autopay_contract.abi
        flex.token.address = mock_token_contract.address

        flex.oracle.connect()
        flex.token.connect()
        flex.autopay.connect()

        # mint token and send to reporter address
        mock_token_contract.faucet(account.address)

        # send eth from brownie address to reporter address for txn fees
        accounts[1].transfer(account.address, "1 ether")

        # approve token to be spent by oracle
        mock_token_contract.approve(mock_flex_contract.address, 100000e18, {"from": account.address})

        _, status = await flex.oracle.write("depositStake", gas_limit=350000, legacy_gas_price=1, _amount=int(10e18))
        # check txn is successful
        assert status.ok

        # approve token to be spent by autopay contract
        mock_token_contract.approve(autopay_contract.address, 100000e18, {"from": account.address})

        return flex


@pytest.fixture(scope="function")
async def setup_datafeed(autopay_contract_setup):
    """Setup and fund all datafeeds for all query ids in telliot"""
    flex = await autopay_contract_setup
    reward = 1 * 10**18
    start_time = TimeStamp.now().ts
    interval = 100
    window = 99
    price_threshold = 0

    count = 0
    for query_id, query_data in zip(CATALOG_QUERY_IDS, CATALOG_QUERY_DATA):
        if "legacy" not in CATALOG_QUERY_IDS[query_id]:
            # legacy is query ids are not encoded the same way as the current query ids
            # so we just avoid it here
            count += 10
            # setup a feed on autopay
            await flex.autopay.write(
                "setupDataFeed",
                gas_limit=3500000,
                legacy_gas_price=1,
                _queryId=query_id,
                _reward=reward,
                _startTime=start_time,
                _interval=interval,
                _window=window,
                _priceThreshold=price_threshold,
                _rewardIncreasePerSecond=0,
                _queryData=query_data,
                _amount=int(count * 10**18),
            )
    return flex


@pytest.fixture(scope="function")
async def setup_one_time_tips(autopay_contract_setup):
    """Tip all query ids in telliot"""
    flex = await autopay_contract_setup
    count = 1  # tip must be greater than zero
    queries = [item for item in zip(CATALOG_QUERY_IDS, CATALOG_QUERY_DATA)]
    for query_id, query_data in queries:

        _, status = await flex.autopay.write(
            "tip",
            gas_limit=3500000,
            legacy_gas_price=1,
            _queryId=query_id,
            _amount=int(count * 10**18),
            _queryData=query_data,
        )
        assert status.ok
        count += 1
    return flex


@pytest.fixture(scope="function")
async def tip_feeds_and_one_time_tips(setup_datafeed, setup_one_time_tips):
    """Initialize both fixtures for datafeeds and one time tips"""
    return await setup_one_time_tips
