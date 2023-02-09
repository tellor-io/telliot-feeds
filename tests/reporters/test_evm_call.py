import pytest
from brownie import chain
from eth_abi import decode_single

from telliot_feeds.queries.evm_call import EVMCall
from telliot_feeds.reporters.tellor_360 import Tellor360Reporter


txn_kwargs = {"gas_limit": 3500000, "legacy_gas_price": 1}
CHAIN_ID = 80001


@pytest.mark.asyncio
async def test_evm_call_e2e(tellor_360, caplog):
    """Test tipping, reporting, and decoding EVMCall query reponse"""
    contracts, account = tellor_360
    r = Tellor360Reporter(
        oracle=contracts.oracle,
        token=contracts.token,
        autopay=contracts.autopay,
        endpoint=contracts.oracle.node,
        account=account,
        chain_id=CHAIN_ID,
        transaction_type=0,
        min_native_token_balance=0,
        datafeed=None,
        check_rewards=True,
    )

    # An improvement would be to create an instance of the EVMCall query
    # that targets a read function on once of the deployed brownie contracts.
    # ( mainly to avoid a network call to your node provider )
    q = EVMCall(
        chainId=1,
        contractAddress="0x88dF592F8eb5D7Bd38bFeF7dEb0fBc02cf3778a0",
        calldata=b"\x18\x16\x0d\xdd",
    )
    # make one-time tip for query
    await r.autopay.write(
        "tip",
        gas_limit=3500000,
        legacy_gas_price=1,
        _queryId=q.query_id,
        _queryData=q.query_data,
        _amount=int(1e18),
    )
    _, status = await r.report_once()
    assert 'Current query: {"type":"EVMCall","chainId":1,"contractAddress":"0x88d' in caplog.text
    assert status.ok

    # read value from tellor oracle
    oracle_rsp, status = await r.oracle.read("getDataBefore", q.query_id, int(chain.time() + 1e9))
    assert status.ok
    assert oracle_rsp is not None
    if_retrieved, value, ts_reported = oracle_rsp
    assert if_retrieved
    assert ts_reported == chain.time()
    print("oracle response:", oracle_rsp)
    assert isinstance(value, bytes)

    # decode EVMCall query response
    v, t = q.value_type.decode(value)
    assert isinstance(v, bytes)
    assert isinstance(t, int)
    trb_total_supply = decode_single("uint256", v)
    assert trb_total_supply > 2390472032948139443578988  # TRB total supply before


@pytest.mark.asyncio
async def test_no_endpoint_for_tipped_chain(tellor_360, caplog):
    """Test reporter doesn't halt if chainId is not supported"""
    contracts, account = tellor_360
    r = Tellor360Reporter(
        oracle=contracts.oracle,
        token=contracts.token,
        autopay=contracts.autopay,
        endpoint=contracts.oracle.node,
        account=account,
        chain_id=CHAIN_ID,
        transaction_type=0,
        min_native_token_balance=0,
        datafeed=None,
        check_rewards=True,
    )

    q = EVMCall(
        chainId=123456789,  # A chain id that doesn't exist
        contractAddress="0x88dF592F8eb5D7Bd38bFeF7dEb0fBc02cf3778a0",
        calldata=b"\x18\x16\x0d\xdd",
    )
    # make one-time tip for query
    await r.autopay.write(
        "tip",
        gas_limit=3500000,
        legacy_gas_price=1,
        _queryId=q.query_id,
        _queryData=q.query_data,
        _amount=int(1e18),
    )
    _, status = await r.report_once()
    assert "Endpoint not found for chain_id=123456789" in caplog.text
    assert not status.ok
