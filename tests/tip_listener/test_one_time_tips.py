"""Test fetching one time tip funded query_data with tip amounts"""
import pytest
from clamfig.base import Registry
from eth_abi import decode_single
from eth_abi import encode_abi
from web3 import Web3

from telliot_feeds.reporters.tip_listener.one_time_tips import OneTimeTips


@pytest.mark.asyncio
async def test_get_one_time_tip_funded_queries(setup_one_time_tips):
    """Test fetching one time funded query data and tip
    Note: not filtered to check if query type exists in catalog
    """
    contract = await setup_one_time_tips
    call = OneTimeTips(contract)
    count = 1
    tips = await call.get_one_time_tip_funded_queries()
    for query_data, tip in tips.items():
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
async def test_nonexisting_qtype_filter(setup_one_time_tips):
    """Test filtering out non existing query type"""
    contract = await setup_one_time_tips
    call = OneTimeTips(contract)
    ftype_name = "FakeType"
    fquery_encoded = encode_abi(["string", "bytes"], [ftype_name, b""])
    fquery_id = Web3.keccak(fquery_encoded)
    fquery_data = Web3.toHex(fquery_encoded)
    _, _ = await contract.write(
        "tip",
        gas_limit=3500000,
        legacy_gas_price=1,
        _queryId=fquery_id,
        _amount=int(5 * 10**18),
        _queryData=fquery_data,
    )
    full_funded_queries_list, status = await call.autopay.read("getFundedSingleTipsInfo")
    assert status.ok
    filtered_queries_list: OneTimeTips = await call.get_one_time_tip_funded_queries()
    assert isinstance(full_funded_queries_list, list)
    assert (fquery_encoded, int(5 * 10**18)) in full_funded_queries_list
    assert (fquery_encoded, int(5 * 10**18)) not in filtered_queries_list


@pytest.mark.asyncio
async def test_no_tips(autopay_contract_setup, caplog: pytest.LogCaptureFixture):
    """Test None by mocking contract call response to return None"""
    contract = await autopay_contract_setup
    call = OneTimeTips(contract)

    await call.get_one_time_tip_funded_queries()
    assert "No one time tip funded queries available" in caplog.text
