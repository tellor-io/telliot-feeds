""" Unit tests for DIVAProtocol queries

Copyright (c) 2021-, Tellor Development Community
Distributed under the terms of the MIT License.
"""
import pytest
from eth_abi import decode_abi
from eth_abi import encode_abi
from hexbytes import HexBytes

from telliot_feeds.queries.diva_protocol import DIVAProtocol


def test_constructor():
    """Validate spot price query."""
    q = DIVAProtocol(
        poolId="0x52a16114f6d8b8213c2a345ce81a7f6d7eb630b7ef25c182817495e2c7d4752e",
        divaDiamond="0xebBAA31B1Ebd727A1a42e71dC15E304aD8905211",
        chainId=3,
    )

    print(q.query_id.hex())
    print(q.query_data)

    exp_query_data = (
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00@\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x0cDIVAProtocol\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00`R\xa1a\x14\xf6\xd8"
        b"\xb8!<*4\\\xe8\x1a\x7fm~\xb60\xb7\xef%\xc1\x82\x81t\x95\xe2\xc7\xd4u.\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\xeb\xba\xa3\x1b\x1e\xbdrz\x1aB\xe7\x1d\xc1^0J\xd8\x90R\x11"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x03"
    )
    assert q.query_data == exp_query_data

    query_type, encoded_param_vals = decode_abi(["string", "bytes"], q.query_data)
    assert query_type == "DIVAProtocol"

    pool_id, diva_diamond, chain_id = decode_abi(["bytes32", "address", "uint256"], encoded_param_vals)
    assert pool_id.hex() == "52a16114f6d8b8213c2a345ce81a7f6d7eb630b7ef25c182817495e2c7d4752e"
    assert diva_diamond == "0xebBAA31B1Ebd727A1a42e71dC15E304aD8905211".lower()
    assert chain_id == 3

    exp = "a1707a0827ec5a90388231bcb750800d462d4c5ccebfff19c684e7cd82336902"
    assert q.query_id.hex() == exp

    q = DIVAProtocol.get_query_from_data(exp_query_data)

    assert isinstance(q, DIVAProtocol)
    assert q.poolId == HexBytes("0x52a16114f6d8b8213c2a345ce81a7f6d7eb630b7ef25c182817495e2c7d4752e")


def test_constructor_error():
    with pytest.raises(ValueError):
        _ = DIVAProtocol(poolId="bingobango", divaDiamond="0xebBAA31B1Ebd727A1a42e71dC15E304aD8905211", chainId=3)


def test_encode_decode_reported_val():
    """Ensure expected encoding/decoding behavior."""
    q = DIVAProtocol(
        poolId="0x52a16114f6d8b8213c2a345ce81a7f6d7eb630b7ef25c182817495e2c7d4752e",
        divaDiamond="0xebBAA31B1Ebd727A1a42e71dC15E304aD8905211",
        chainId=3,
    )

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
