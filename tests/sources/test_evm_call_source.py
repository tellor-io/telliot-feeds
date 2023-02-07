import pytest
from telliot_core.apps.telliot_config import TelliotConfig

from telliot_feeds.sources.evm_call import EVMCallSource


@pytest.mark.asyncio
async def test_source():
    """Test initialization of EVMCallSource."""
    s = EVMCallSource()
    assert s.chain_id is None
    assert s.contract_address is None
    assert s.calldata is None
    assert s.web3 is None
    assert s.cfg is not None
    assert s.cfg.main.chain_id == TelliotConfig().main.chain_id

    s2 = EVMCallSource(
        chain_id=80001,
        contract_address="0x88dF592F8eb5D7Bd38bFeF7dEb0fBc02cf3778a0",
        calldata=b"\x18\x16\x0d\xdd",
    )
    assert s2.chain_id == 80001
    assert s2.contract_address == "0x88dF592F8eb5D7Bd38bFeF7dEb0fBc02cf3778a0"
    assert s2.calldata == b"\x18\x16\x0d\xdd"

    # test update_web3
    s2.update_web3()
    assert s2.web3 is not None

    # test get_response
    response = s2.get_response()
    assert response is not None
    assert isinstance(response, bytes)

    # test fetch_new_datapoint
    v, t = await s2.fetch_new_datapoint()
    assert v is not None
    assert t is not None
