""" Unit tests for DIVAProtocolPolygon queries

Copyright (c) 2021-, Tellor Development Community
Distributed under the terms of the MIT License.
"""
from eth_abi import decode_abi
from eth_abi import encode_abi

from telliot_core.queries.diva_protocol import DIVAProtocolPolygon


def test_constructor():
    """Validate spot price query."""
    q = DIVAProtocolPolygon(poolId=156)

    # print(q.query_id.hex())
    # print(q.query_data)

    exp_query_data = (
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00@\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x13DIVAProtocolPolygon"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00 \x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x9c"
    )
    assert q.query_data == exp_query_data

    query_type, encoded_param_vals = decode_abi(["string", "bytes"], q.query_data)
    assert query_type == "DIVAProtocolPolygon"

    pool_id = decode_abi([q.abi[0]["type"]], encoded_param_vals)[0]
    assert pool_id == 156

    exp = "551179c46e6a88b7e034b039dbe264685f1895607515ddda71daffe9e7814c20"
    assert q.query_id.hex() == exp

    q = DIVAProtocolPolygon.get_query_from_data(exp_query_data)

    assert isinstance(q, DIVAProtocolPolygon)
    assert q.poolId == 156


def test_encode_decode_reported_val():
    """Ensure expected encoding/decoding behavior."""
    q = DIVAProtocolPolygon(poolId=156)

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
