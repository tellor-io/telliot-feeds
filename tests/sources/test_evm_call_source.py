import pytest
from eth_abi import decode_single
from hexbytes import HexBytes
from telliot_core.apps.telliot_config import TelliotConfig

from telliot_feeds.sources.evm_call import EVMCallSource


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
    s2.update_web3()
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
    s.update_web3()

    """Test non getter calldata"""
    s.calldata = b"\x3a\x0c\xe3\x42"  # calldata for updateStakeAmount()
    s.contractAddress = "0xD9157453E2668B2fc45b7A803D3FEF3642430cC0"  # Oracle contract

    # test get_response
    response = s.get_response()
    assert response == (None, None)

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
