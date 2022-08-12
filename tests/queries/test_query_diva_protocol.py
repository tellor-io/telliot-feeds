""" Unit tests for DIVAProtocol queries

Copyright (c) 2021-, Tellor Development Community
Distributed under the terms of the MIT License.
"""
import pytest
from eth_abi import decode_abi
from eth_abi import encode_abi

from telliot_feeds.queries.diva_protocol import DIVAProtocol


def test_constructor():
    """Validate spot price query."""
    q = DIVAProtocol(poolId=1234, divaDiamond="0xebBAA31B1Ebd727A1a42e71dC15E304aD8905211", chainId=3)

    print(q.query_id.hex())
    print(q.query_data)

    exp_query_data = (
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00@\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x0cDIVAProtocol\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00`\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x04\xd2\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xeb\xba\xa3\x1b\x1e"
        b"\xbdrz\x1aB\xe7\x1d\xc1^0J\xd8\x90R\x11\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x03"
    )
    assert q.query_data == exp_query_data

    query_type, encoded_param_vals = decode_abi(["string", "bytes"], q.query_data)
    assert query_type == "DIVAProtocol"

    pool_id, diva_diamond, chain_id = decode_abi(["uint256", "address", "uint256"], encoded_param_vals)
    assert pool_id == 1234
    assert diva_diamond == "0xebBAA31B1Ebd727A1a42e71dC15E304aD8905211".lower()
    assert chain_id == 3

    exp = "964520ccd4ad6970a627e4e8834f38cb2ee5f4997aa7646e3ef738e2e6df14dc"
    assert q.query_id.hex() == exp

    q = DIVAProtocol.get_query_from_data(exp_query_data)

    assert isinstance(q, DIVAProtocol)
    assert q.poolId == 1234


def test_constructor_error():
    with pytest.raises(ValueError) as excinfo:
        _ = DIVAProtocol(poolId=1234, divaDiamond="blah", chainId=3)

    assert "when sending a str, it must be a hex string. Got: 'blah'" in str(excinfo.value)


def test_encode_decode_reported_val():
    """Ensure expected encoding/decoding behavior."""
    q = DIVAProtocol(poolId=1234, divaDiamond="0xebBAA31B1Ebd727A1a42e71dC15E304aD8905211", chainId=3)

    # Reference asset example: ETH/USD ($2,819.35)
    # Collateral token example: DAI/USD ($0.9996)
    data = [2819.35, 0.9996]

    data2 = [int(v * 1e18) for v in data]
    d1 = encode_abi(["uint256", "uint256"], data2)
    submit_value = q.value_type.encode(data)

    assert isinstance(submit_value, bytes)
    assert submit_value == d1
    print(submit_value.hex())

    decoded_data = q.value_type.decode(submit_value)
    assert isinstance(decoded_data, list)
    assert isinstance(decoded_data[0], float)
    assert isinstance(decoded_data[1], float)
    assert decoded_data == data
