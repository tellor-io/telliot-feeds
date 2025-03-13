import os
from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest
from hexbytes import HexBytes
from telliot_core.apps.core import RPCEndpoint
from telliot_core.apps.telliot_config import TelliotConfig
from telliot_core.model.endpoints import EndpointList
from telliot_core.utils.response import ResponseStatus
from web3 import Web3

from telliot_feeds.constants import ETHEREUM_CHAINS
from telliot_feeds.datafeed import DataFeed
from telliot_feeds.dtypes.value_type import decode_single
from telliot_feeds.feeds.evm_call_feed import evm_call_feed_example
from telliot_feeds.queries.evm_call import EVMCall
from telliot_feeds.reporters.tellor_360 import Tellor360Reporter
from telliot_feeds.sources.evm_call import EVMCallSource

txn_kwargs = {"gas_limit": 3500000, "legacy_gas_price": 1}
CHAIN_ID = 80001


@pytest.mark.asyncio
async def test_evm_call_e2e(tellor_360, caplog, chain, monkeypatch):
    """Test tipping, reporting, and decoding EVMCall query reponse"""
    with patch("telliot_feeds.utils.query_search_utils.feed_from_catalog_feeds") as mock_feed:
        cfg = TelliotConfig()
        custom_endpoint = RPCEndpoint(
            chain_id=1, network="mainnet", url=f"https://mainnet.infura.io/v3/{os.environ['INFURA_API_KEY']}"
        )
        cfg.endpoints = EndpointList(endpoints=[custom_endpoint])

        feed = evm_call_feed_example
        feed.query = EVMCall(
            chainId=1, contractAddress="0x88dF592F8eb5D7Bd38bFeF7dEb0fBc02cf3778a0", calldata=b"\x18\x16\r\xdd"
        )
        feed.source = EVMCallSource(
            chainId=1, contractAddress="0x88dF592F8eb5D7Bd38bFeF7dEb0fBc02cf3778a0", calldata=b"\x18\x16\r\xdd", cfg=cfg
        )
        mock_feed.return_value = feed
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
            ignore_tbr=False,
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
        _, status = await r.token.write(
            "approve",
            gas_limit=350000,
            legacy_gas_price=1,
            spender=r.autopay.address,
            amount=int(1e18),
        )
        assert status.ok
        _, status = await r.autopay.write(
            "tip",
            gas_limit=3500000,
            legacy_gas_price=1,
            _queryId=q.query_id,
            _queryData=q.query_data,
            _amount=int(1e18),
        )
        assert status.ok

        _, status = await r.report_once()
        assert 'Current query: {"type":"EVMCall","chainId":1,"contractAddress":"0x88d' in caplog.text
        assert status.ok

        # read value from tellor oracle
        oracle_rsp, status = await r.oracle.read("getDataBefore", q.query_id, int(chain.pending_timestamp + 1e9))
        assert status.ok
        assert oracle_rsp is not None
        if_retrieved, value, ts_reported = oracle_rsp
        assert if_retrieved
        assert ts_reported == pytest.approx(chain.pending_timestamp, 1)
        print("oracle response:", oracle_rsp)
        assert isinstance(value, bytes)

        # decode EVMCall query response
        v, t = q.value_type.decode(value)
        assert isinstance(v, bytes)
        assert isinstance(t, int)
        trb_total_supply = decode_single("uint256", v)
        assert trb_total_supply > 2390472032948139443578988  # TRB total supply before


@pytest.mark.asyncio
async def test_no_endpoint_for_tipped_chain(tellor_360, chain, caplog):
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
        ignore_tbr=False,
    )

    q = EVMCall(
        chainId=123456789,  # A chain id that doesn't exist
        contractAddress="0x88dF592F8eb5D7Bd38bFeF7dEb0fBc02cf3778a0",
        calldata=b"\x18\x16\x0d\xdd",
    )
    # make one-time tip for query
    _, status = await r.token.write(
        "approve",
        gas_limit=350000,
        legacy_gas_price=1,
        spender=r.autopay.address,
        amount=int(1e18),
    )
    assert status.ok

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


@pytest.mark.asyncio
async def test_bad_contract_address(tellor_360, chain, caplog, monkeypatch):
    """Test reporter doesn't halt if chainId is not supported"""
    cfg = TelliotConfig()
    custom_endpoint = RPCEndpoint(
        chain_id=1, network="mainnet", url=f"https://mainnet.infura.io/v3/{os.environ['INFURA_API_KEY']}"
    )
    cfg.endpoints = EndpointList(endpoints=[custom_endpoint])

    contracts, account = tellor_360
    invalid_address = "0x1234567890123456789012345678901234567890"

    feed = evm_call_feed_example
    feed.query.contractAddress = invalid_address
    source = EVMCallSource(
        chainId=feed.source.chainId, calldata=feed.source.calldata, contractAddress=invalid_address, cfg=cfg
    )
    feed.source = source

    r = Tellor360Reporter(
        oracle=contracts.oracle,
        token=contracts.token,
        autopay=contracts.autopay,
        endpoint=contracts.oracle.node,
        account=account,
        chain_id=CHAIN_ID,
        transaction_type=0,
        min_native_token_balance=0,
        datafeed=feed,
        check_rewards=True,
        gas_limit=350000,
        ignore_tbr=False,
    )

    _, status = await r.report_once()
    assert f"Invalid contract address: {invalid_address}, no bytecode, submitting empty bytes" in caplog.text
    assert status.ok


@pytest.mark.asyncio
async def test_short_call_data(tellor_360, caplog):
    """Test when calldata is less than 4 bytes"""
    cfg = TelliotConfig()
    custom_endpoint = RPCEndpoint(
        chain_id=1, network="mainnet", url=f"https://mainnet.infura.io/v3/{os.environ['INFURA_API_KEY']}"
    )
    cfg.endpoints = EndpointList(endpoints=[custom_endpoint])

    contracts, account = tellor_360
    invalid_calldata = HexBytes("0x165c4a")  # less than 4 bytes

    feed = evm_call_feed_example
    feed.query.calldata = invalid_calldata
    source = EVMCallSource(
        chainId=feed.source.chainId, calldata=invalid_calldata, contractAddress=feed.source.contractAddress, cfg=cfg
    )
    feed.source = source

    r = Tellor360Reporter(
        oracle=contracts.oracle,
        token=contracts.token,
        autopay=contracts.autopay,
        endpoint=contracts.oracle.node,
        account=account,
        chain_id=CHAIN_ID,
        transaction_type=0,
        min_native_token_balance=0,
        datafeed=feed,
        check_rewards=True,
        gas_limit=350000,
        ignore_tbr=False,
    )

    _, status = await r.report_once()
    assert f"Invalid calldata: {invalid_calldata!r}, too short, submitting empty bytes" in caplog.text
    assert status.ok


@pytest.mark.asyncio
async def test_function_doesnt_exist(tellor_360, caplog, chain):
    """Test function doesn't exist in contract"""
    cfg = TelliotConfig()
    custom_endpoint = RPCEndpoint(
        chain_id=1, network="mainnet", url=f"https://mainnet.infura.io/v3/{os.environ['INFURA_API_KEY']}"
    )
    cfg.endpoints = EndpointList(endpoints=[custom_endpoint])

    contracts, account = tellor_360
    feed = evm_call_feed_example
    non_existing_sig = HexBytes("0x165c4a16")
    source = EVMCallSource(
        chainId=feed.source.chainId,
        calldata=non_existing_sig,
        contractAddress="0x88dF592F8eb5D7Bd38bFeF7dEb0fBc02cf3778a0",
        cfg=cfg,
    )
    feed.source = source

    r = Tellor360Reporter(
        oracle=contracts.oracle,
        token=contracts.token,
        autopay=contracts.autopay,
        endpoint=contracts.oracle.node,
        account=account,
        chain_id=CHAIN_ID,
        transaction_type=0,
        min_native_token_balance=0,
        datafeed=feed,
        check_rewards=True,
        gas_limit=350000,
        ignore_tbr=False,
    )
    r.check_reporter_lock = AsyncMock(lambda: ResponseStatus())
    chain.pending_timestamp += 43201
    _, status = await r.report_once()
    assert f"function selector: {non_existing_sig!r}, not found in bytecode, submitting empty bytes" in caplog.text
    assert status.ok


@pytest.mark.asyncio
async def test_non_view_evm_call(tellor_360, chain, caplog):
    """Test for when the call is to a non-view function,
    nothing should be submitted to oracle since its hard to tell if a false
    negative could happen
    """
    contracts, account = tellor_360
    signature = Web3.keccak(text="updateStakeAmount()")[:4].hex()
    _amount = Web3.to_hex(10)[2:].zfill(64)
    non_view_call_data = HexBytes(signature + _amount)
    cfg = TelliotConfig()
    cfg.endpoints.endpoints.append(RPCEndpoint(chain_id=1337, url="http://localhost:8545"))
    feed = DataFeed(
        query=EVMCall(chainId=1337, contractAddress=contracts.oracle.address, calldata=non_view_call_data),
        source=EVMCallSource(
            chainId=1337, contractAddress=contracts.oracle.address, calldata=non_view_call_data, cfg=cfg
        ),
    )
    ETHEREUM_CHAINS.add(1337)
    r = Tellor360Reporter(
        oracle=contracts.oracle,
        token=contracts.token,
        autopay=contracts.autopay,
        endpoint=contracts.oracle.node,
        account=account,
        chain_id=1337,
        transaction_type=0,
        min_native_token_balance=0,
        datafeed=feed,
        check_rewards=True,
        gas_limit=350000,
        ignore_tbr=False,
    )
    _, status = await r.report_once()
    assert "Result is empty bytes, call might be to a non-view function" in caplog.text
    assert not status.ok
