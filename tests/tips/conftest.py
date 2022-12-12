import pytest
from brownie import accounts
from brownie import Autopay
from brownie import TellorFlex360
from telliot_core.apps.core import TelliotCore
from telliot_core.utils.timestamp import TimeStamp

from telliot_feeds.reporters.tips import CATALOG_QUERY_DATA
from telliot_feeds.reporters.tips import CATALOG_QUERY_IDS


trb_id = "0x5c13cd9c97dbb98f2429c101a2a8150e6c7a0ddaff6124ee176a3a411067ded0"
txn_kwargs = {"gas_limit": 3500000, "legacy_gas_price": 1}
account_fake = accounts.add("023861e2ceee1ea600e43cbd203e9e01ea2ed059ee3326155453a1ed3b1113a9")


@pytest.fixture(scope="function")
def tellorflex_360_contract(mock_token_contract):
    return account_fake.deploy(
        TellorFlex360,
        mock_token_contract.address,
        1,
        1,
        1,
        trb_id,
    )


@pytest.fixture(scope="function")
def autopay_contract(tellorflex_360_contract, mock_token_contract, query_data_storage_contract):
    """mock payments(Autopay) contract for tipping and claiming tips"""
    return accounts[0].deploy(
        Autopay,
        tellorflex_360_contract.address,
        mock_token_contract.address,
        query_data_storage_contract.address,
        20,
    )


@pytest.fixture(scope="function")
async def autopay_contract_setup(
    mumbai_test_cfg, tellorflex_360_contract, autopay_contract, mock_token_contract, multicall_contract
):
    async with TelliotCore(config=mumbai_test_cfg) as core:

        # get PubKey and PrivKey from config files
        account = core.get_account()

        flex = core.get_tellor360_contracts()
        flex.oracle.address = tellorflex_360_contract.address
        flex.oracle.abi = tellorflex_360_contract.abi
        flex.autopay.address = autopay_contract.address
        flex.autopay.abi = autopay_contract.abi
        flex.token.address = mock_token_contract.address

        flex.oracle.connect()
        flex.token.connect()
        flex.autopay.connect()

        # mint token and send to reporter address
        mock_token_contract.mint(account.address, 100000e18)

        # send eth from brownie address to reporter address for txn fees
        accounts[1].transfer(account.address, "1 ether")
        # init governance address
        await flex.oracle.write("init", _governanceAddress=accounts[0].address, **txn_kwargs)

        # approve token to be spent by oracle
        mock_token_contract.approve(tellorflex_360_contract.address, 100000e18, {"from": account.address})

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
    for query_id, query_data in zip(CATALOG_QUERY_IDS, CATALOG_QUERY_DATA):
        # legacy is query ids are not encoded the same way as the current query ids
        # so we just avoid it here
        if "legacy" not in CATALOG_QUERY_IDS[query_id]:
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
