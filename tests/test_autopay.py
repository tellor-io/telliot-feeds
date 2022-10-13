import pytest
from brownie import accounts
from brownie import chain
from brownie.network.account import Account
from eth_abi import encode_single
from telliot_core.apps.core import TelliotCore
from telliot_core.utils.response import ResponseStatus
from telliot_core.utils.timestamp import TimeStamp
from web3 import Web3

from telliot_feeds.queries.query_catalog import query_catalog
from telliot_feeds.reporters.reporter_autopay_utils import autopay_suggested_report
from telliot_feeds.reporters.reporter_autopay_utils import get_feed_tip


@pytest.mark.asyncio
async def test_main(
    mumbai_test_cfg, mock_flex_contract, mock_autopay_contract, mock_token_contract, multicall_contract
):
    async with TelliotCore(config=mumbai_test_cfg) as core:

        # get PubKey and PrivKey from config files
        account = core.get_account()

        flex = core.get_tellorflex_contracts()
        flex.oracle.address = mock_flex_contract.address
        flex.autopay.address = mock_autopay_contract.address
        flex.autopay.abi = mock_autopay_contract.abi
        flex.token.address = mock_token_contract.address

        flex.oracle.connect()
        flex.token.connect()
        flex.autopay.connect()

        # mint token and send to reporter address
        mock_token_contract.mint(account.address, 1000e18)
        assert mock_token_contract.balanceOf(account.address) == 1000e18

        # send eth from brownie address to reporter address for txn fees
        accounts[0].transfer(account.address, "1 ether")
        assert Account(account.address).balance() == 1e18

        # check governance address is brownie address
        governance_address = await flex.oracle.get_governance_address()
        assert governance_address == accounts[0]

        # check stake amount is ten
        stake_amount = await flex.oracle.get_stake_amount()
        assert stake_amount == 10

        # approve token to be spent by oracle
        mock_token_contract.approve(mock_flex_contract.address, 50e18, {"from": account.address})

        # staking to oracle transaction
        timestamp = TimeStamp.now().ts
        _, status = await flex.oracle.write("depositStake", gas_limit=350000, legacy_gas_price=1, _amount=10 * 10**18)
        # check txn is successful
        assert status.ok

        # check staker information
        staker_info, status = await flex.oracle.get_staker_info(Web3.toChecksumAddress(account.address))
        assert isinstance(status, ResponseStatus)
        assert status.ok
        assert staker_info == [pytest.approx(timestamp, 200), 10e18, 0, 0, 0]

        # get suggestion from telliot on query with highest tip
        suggested_qtag, tip = await autopay_suggested_report(flex.autopay)
        assert suggested_qtag is None
        assert tip is None

        # mkr query id and query data
        mkr_query_id = query_catalog._entries["mkr-usd-spot"].query.query_id
        mkr_query_data = "0x" + query_catalog._entries["mkr-usd-spot"].query.query_data.hex()
        # approve token to be spent by autopay contract
        mock_token_contract.approve(mock_autopay_contract.address, 500e18, {"from": account.address})
        _, status = await flex.autopay.write(
            "tip",
            gas_limit=3500000,
            legacy_gas_price=1,
            _queryId="0x" + mkr_query_id.hex(),
            _amount=int(10e18),
            _queryData=mkr_query_data,
        )
        # check txn is successful
        assert status.ok

        # submit a tip in autopay for reporter to report mkr/usd price
        current_tip, status = await flex.autopay.get_current_tip(mkr_query_id)
        # check success of txn
        assert status.ok
        # check tip amount
        assert current_tip == 10e18

        # get suggestion from telliot on query with highest tip
        suggested_qtag, tip = await autopay_suggested_report(flex.autopay)
        assert suggested_qtag == "mkr-usd-spot"
        assert tip == 10e18

        # query id and query data for ric
        ric_query_id = query_catalog._entries["ric-usd-spot"].query_id
        ric_query_data = "0x" + query_catalog._entries["ric-usd-spot"].query.query_data.hex()

        _, status = await flex.autopay.write(
            "tip",
            gas_limit=3500000,
            legacy_gas_price=1,
            _queryId=ric_query_id,
            _amount=int(20e18),
            _queryData=ric_query_data,
        )

        assert status.ok

        current_tip, status = await flex.autopay.get_current_tip(ric_query_id)
        assert status.ok
        assert current_tip == 20e18

        # get suggestion from telliot on query with highest tip
        suggested_qtag, tip = await autopay_suggested_report(flex.autopay)
        assert suggested_qtag == "ric-usd-spot"
        assert tip == 20e18

        # variables for feed setup and to get feedId
        trb_query_id = query_catalog._entries["trb-usd-spot"].query_id
        reward = 30 * 10**18
        interval = 100
        window = 99
        price_threshold = 0
        trb_query_data = "0x" + query_catalog._entries["trb-usd-spot"].query.query_data.hex()

        # setup a feed on autopay
        response, status = await flex.autopay.write(
            "setupDataFeed",
            gas_limit=3500000,
            legacy_gas_price=1,
            _queryId=trb_query_id,
            _reward=reward,
            _startTime=timestamp,
            _interval=interval,
            _window=window,
            _priceThreshold=price_threshold,
            _rewardIncreasePerSecond=0,
            _queryData=trb_query_data,
            _amount=50 * 10**18,
        )
        assert status.ok

        feed_id = response.logs[1].topics[2].hex()

        # get suggestion from telliot on query with highest tip
        suggested_qtag, tip = await autopay_suggested_report(flex.autopay)
        assert suggested_qtag == "trb-usd-spot"
        assert tip == 30e18

        tips = await get_feed_tip(query_catalog._entries["trb-usd-spot"].query.query_id, flex.autopay)
        assert tips == 30e18

        # submit report to oracle to get tip
        _, status = await flex.oracle.write(
            "submitValue",
            gas_limit=350000,
            legacy_gas_price=1,
            _queryId=trb_query_id,
            _value="0x" + encode_single("(uint256)", [3000]).hex(),
            _nonce=0,
            _queryData=trb_query_data,
        )
        chain.snapshot()

        # get suggestion from telliot on query with highest tip
        suggested_qtag, tip = await autopay_suggested_report(flex.autopay)
        assert suggested_qtag == "ric-usd-spot"
        assert tip == 20e18

        # fast forward to avoid claiming tips buffer 12hr
        chain.sleep(43201)

        # get timestamp trb's reported value
        read_timestamp, status = await flex.autopay.read("getCurrentValue", _queryId=trb_query_id)
        assert status.ok

        _, status = await flex.autopay.write(
            "claimTip",
            gas_limit=350000,
            legacy_gas_price=1,
            _feedId=feed_id,
            _queryId=trb_query_id,
            _timestamps=[read_timestamp[2]],
        )
        assert status.ok

        # get suggestion from telliot on query with highest tip
        suggested_qtag, tip = await autopay_suggested_report(flex.autopay)
        assert suggested_qtag == "ric-usd-spot"
        assert tip == 20e18

        # submit report for onetime tip to oracle
        # should reserve tip for first reporter
        _, status = await flex.oracle.write(
            "submitValue",
            gas_limit=350000,
            legacy_gas_price=1,
            _queryId=ric_query_id,
            _value="0x" + encode_single("(uint256)", [1000]).hex(),
            _nonce=0,
            _queryData=ric_query_data,
        )
        assert status.ok

        # get suggestion from telliot on query with highest tip
        suggested_qtag, tip = await autopay_suggested_report(flex.autopay)
        assert suggested_qtag == "mkr-usd-spot"
        assert tip == 10e18

        # fast forward to avoid reporter time lock
        chain.sleep(61)

        # submit report for onetime tip to oracle
        # should reserve tip for first reporter
        _, status = await flex.oracle.write(
            "submitValue",
            gas_limit=350000,
            legacy_gas_price=1,
            _queryId=mkr_query_id,
            _value="0x" + encode_single("(uint256)", [1000]).hex(),
            _nonce=0,
            _queryData=mkr_query_data,
        )
        assert status.ok

        # get suggestion from telliot on query with highest tip
        suggested_qtag, tip = await autopay_suggested_report(flex.autopay)
        assert suggested_qtag is None
        assert tip is None
