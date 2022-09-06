"""Test fetching one time tip funded query_data with tip amounts"""
import pytest
from brownie import accounts
from clamfig.base import Registry
from eth_abi import decode_single
from eth_abi import encode_abi
from telliot_core.apps.core import TelliotCore
from telliot_core.utils.response import ResponseStatus
from web3 import Web3

from telliot_feeds.queries.query_catalog import query_catalog
from telliot_feeds.reporters.tip_listener.one_time_tips import OneTimeTips


CATALOG_QUERY_IDS = {query_catalog._entries[tag].query.query_id: tag for tag in query_catalog._entries}
CATALOG_QUERY_DATA = {query_catalog._entries[tag].query.query_data: tag for tag in query_catalog._entries}


@pytest.fixture
async def one_time_tips(mumbai_test_cfg, mock_flex_contract, mock_autopay_contract, mock_token_contract):
    async with TelliotCore(config=mumbai_test_cfg) as core:

        # get PubKey and PrivKey from config files
        account = core.get_account()

        flex = core.get_tellorflex_contracts()
        flex.oracle.address = mock_flex_contract.address
        flex.oracle.abi = mock_flex_contract.abi
        flex.autopay.address = mock_autopay_contract.address
        flex.autopay.abi = mock_autopay_contract.abi
        flex.token.address = mock_token_contract.address

        flex.oracle.connect()
        flex.token.connect()
        flex.autopay.connect()

        # mint token and send to reporter address
        mock_token_contract.mint(account.address, 1000e18)

        # send eth from brownie address to reporter address for txn fees
        accounts[0].transfer(account.address, "1 ether")

        # check governance address is brownie address
        _, status = await flex.oracle.write("init", _governanceAddress=accounts[0].address, gas_limit=350000, legacy_gas_price=1)
        assert status.ok

        # approve token to be spent by oracle
        mock_token_contract.approve(mock_flex_contract.address, 500e18, {"from": account.address})

        # staking to oracle transaction
        _, status = await flex.oracle.write("depositStake", gas_limit=350000, legacy_gas_price=1, _amount=10 * 10**18)
        # check txn is successful
        assert status.ok

        # approve token to be spent by autopay contract
        mock_token_contract.approve(mock_autopay_contract.address, 500e18, {"from": account.address})
        count = 1  # tip must be greater than zero
        for query_id, query_data in zip(CATALOG_QUERY_IDS, CATALOG_QUERY_DATA):
            if "legacy" not in CATALOG_QUERY_IDS[query_id]:
                # legacy is query ids are not encoded the same way as the current query ids
                # so we just avoid it here
                _, status = await flex.autopay.write(
                    "tip",
                    gas_limit=3500000,
                    legacy_gas_price=1,
                    _queryId=query_id,
                    _amount=int(int(count) * 10**18),
                    _queryData=query_data,
                )
                assert status.ok
                count += 1

    return OneTimeTips(flex.autopay)


@pytest.mark.asyncio
async def test_get_one_time_tip_funded_queries(one_time_tips):
    """Test fetching one time funded query data and tip
    Note: not filtered to check if query type exists in catalog
    """
    call: OneTimeTips = await one_time_tips
    count = 1
    tips = await call.get_one_time_tip_funded_queries()
    for query_data, tip in tips:
        try:
            query_data = decode_single("(string,bytes)", query_data)[0]
        except OverflowError:
            # string query for some reason encoding isn't the same as the others
            import ast

            query_data = ast.literal_eval(query_data.decode("utf-8"))["type"]
        assert tip == int(int(count) * 10**18)
        assert query_data in Registry.registry
        count += 1
    assert len(tips) == count - 1


@pytest.mark.asyncio
async def test_nonexisting_qtype_filter(one_time_tips):
    """Test filtering out non existing query type"""
    call: OneTimeTips = await one_time_tips
    ftype_name = "FakeType"
    fquery_encoded = encode_abi(["string", "bytes"], [ftype_name, b""])
    fquery_id = Web3.keccak(fquery_encoded)
    fquery_data = Web3.toHex(fquery_encoded)
    _, _ = await call.autopay.write(
        "tip",
        gas_limit=3500000,
        legacy_gas_price=1,
        _queryId=fquery_id,
        _amount=int(5 * 10**18),
        _queryData=fquery_data,
    )
    full_funded_queries_list, status = await call.autopay_function_call("getFundedSingleTipsInfo")
    assert status.ok
    filtered_queries_list: OneTimeTips = await call.get_one_time_tip_funded_queries()
    assert isinstance(full_funded_queries_list, list)
    assert (fquery_encoded, int(5 * 10**18)) in full_funded_queries_list
    assert (fquery_encoded, int(5 * 10**18)) not in filtered_queries_list


@pytest.mark.asyncio
async def test_no_tips(one_time_tips, caplog: pytest.LogCaptureFixture):
    """Test None by mocking contract call response to return None"""
    call: OneTimeTips = await one_time_tips

    async def dummy_function(_=None):
        return None, ResponseStatus

    call.autopay_function_call = dummy_function
    await call.get_one_time_tip_funded_queries()
    assert "No one time tip funded queries available" in caplog.text
