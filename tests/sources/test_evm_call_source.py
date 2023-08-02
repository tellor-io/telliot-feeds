import pytest
from eth_abi import decode_single
from hexbytes import HexBytes
from telliot_core.apps.telliot_config import TelliotConfig

from telliot_feeds.reporters.tellor_360 import Tellor360Reporter
from telliot_feeds.sources.evm_call import EVMCallSource
from telliot_feeds.utils.source_utils import update_web3


@pytest.mark.asyncio
async def test_not_injecting_middlware_twice(caplog):
    """Test that reusing a POA chain does not crash from middleware"""

    s = EVMCallSource()
    s.chainId = 80001  # a POA chain, so it will raise web3.exceptions.ExtraDataLengthError
    s.web3 = update_web3(s.chainId, s.cfg)

    # We will use `getCurrentValue` on the ETH/USD query id
    s.calldata = bytes.fromhex("adf1639d83a7f3d48786ac2667503a61e8c415438ed2922eb86a2906e4ee66d9a2ce4992")
    s.contractAddress = "0xD9157453E2668B2fc45b7A803D3FEF3642430cC0"

    s.get_response()
    assert "It is quite likely that you are connected to a POA chain." in caplog.text

    s.get_response()
    assert "Layer already has middleware with identifier: geth_poa_middleware" not in caplog.text


@pytest.mark.asyncio
async def test_source():
    """Test initialization of EVMCallSource."""
    s = EVMCallSource()
    assert s.chainId is None
    assert s.contractAddress is None
    assert s.calldata is None
    assert s.web3 is None
    assert s.cfg is not None
    assert s.cfg.main.chain_id == TelliotConfig().main.chain_id

    s2 = EVMCallSource(
        chainId=1,
        contractAddress="0x88dF592F8eb5D7Bd38bFeF7dEb0fBc02cf3778a0",
        calldata=b"\x18\x16\x0d\xdd",
    )
    assert s2.chainId == 1
    assert s2.contractAddress == "0x88dF592F8eb5D7Bd38bFeF7dEb0fBc02cf3778a0"
    assert s2.calldata == b"\x18\x16\x0d\xdd"

    # test update_web3
    s2.web3 = update_web3(s2.chainId, s2.cfg)
    assert s2.web3 is not None

    # test get_response
    response = s2.get_response()
    assert response is not None
    assert isinstance(response[0], HexBytes)
    assert isinstance(response[1], int)

    v, t = response
    assert v is not None
    assert t is not None
    assert isinstance(v, bytes)
    assert isinstance(t, int)
    assert decode_single("uint256", v) > 2390472032948139443578988  # an earlier total supply of TRB

    # test fetch_new_datapoint
    v, t = await s2.fetch_new_datapoint()
    assert v is not None
    assert t is not None


@pytest.mark.asyncio
async def test_non_getter_calldata():
    """Test if calldata is not for a getter function."""
    s = EVMCallSource()
    s.chainId = 80001
    s.web3 = update_web3(s.chainId, s.cfg)

    """Test non getter calldata"""
    s.calldata = b"\x3a\x0c\xe3\x42"  # calldata for updateStakeAmount()
    s.contractAddress = "0xD9157453E2668B2fc45b7A803D3FEF3642430cC0"  # Oracle contract

    # test get_response
    response = s.get_response()
    assert response is None

    """Test getter calldata"""
    s.calldata = b"\x73\x25\x24\x94"  # calldata for getGovernanceAddress()
    response = s.get_response()
    assert response is not None
    assert isinstance(response[0], HexBytes)
    assert isinstance(response[1], int)

    v, t = response
    assert v is not None
    assert t is not None
    assert isinstance(v, bytes)
    assert isinstance(t, int)
    assert decode_single("address", v) == "0x46038969d7dc0b17bc72137d07b4ede43859da45"


@pytest.mark.asyncio
async def test_report_for_bad_calldata(tellor_360):
    """Test report empty bytes for bad calldata."""
    contracts, account = tellor_360

    from telliot_feeds.datafeed import DataFeed
    from telliot_feeds.queries.evm_call import EVMCall
    from telliot_feeds.sources.evm_call import EVMCallSource

    chain_id = 1
    contract_address = "0x88dF592F8eb5D7Bd38bFeF7dEb0fBc02cf3778a0"  # good contract address
    calldata = b"\x18\x16\x0d"  # bad calldata

    bad_calldata_feed = DataFeed(
        query=EVMCall(
            chainId=chain_id,
            contractAddress=contract_address,
            calldata=calldata,
        ),
        source=EVMCallSource(
            chainId=chain_id,
            contractAddress=contract_address,
            calldata=calldata,
        ),
    )

    r = Tellor360Reporter(
        oracle=contracts.oracle,
        token=contracts.token,
        autopay=contracts.autopay,
        endpoint=contracts.oracle.node,
        account=account,
        chain_id=80001,
        transaction_type=0,
        legacy_gas_price=1,
        gas_limit=350000,
        min_native_token_balance=0,
        datafeed=bad_calldata_feed,
        check_rewards=False,
    )
    await r.report_once()
    # call r.ensure_staked to update staker info
    await r.ensure_staked()
    assert r.stake_info.reports_count == 1


def test_evm_call_on_previous_block():
    """Test an EVMCall on a block that isn't the latest block"""

    s = EVMCallSource()
    s.chainId = 1
    s.web3 = update_web3(s.chainId, s.cfg)

    # We will use `getCurrentValue` on the ETH/USD query id
    s.calldata = bytes.fromhex("adf1639d83a7f3d48786ac2667503a61e8c415438ed2922eb86a2906e4ee66d9a2ce4992")
    s.contractAddress = "0xD9157453E2668B2fc45b7A803D3FEF3642430cC0"

    current_value, current_timestamp = s.get_response()

    old_block_number = s.web3.eth.get_block_number() - 2000

    previous_value, previous_timestamp = s.get_response(old_block_number)

    assert current_value != previous_value
    assert current_timestamp != previous_timestamp
