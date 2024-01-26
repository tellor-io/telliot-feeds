""" Unit tests for EVMBalance Query

Copyright (c) 2024-, Tellor Development Community
Distributed under the terms of the MIT License.
"""
from eth_abi import decode_abi

from telliot_feeds.queries.evm_balance import EVMBalance


def test_evm_balance_query():
    """Validate evm balance query"""
    q = EVMBalance(
        chainId=11155111,
        evmAddress="0x210766226c54cdd6bd0401749d43e7a5585e3868",
        timestamp=1706302197,
    )
    assert q.value_type.abi_type == "uint256"
    assert q.value_type.packed is False

    exp_abi = bytes.fromhex(
        "0000000000000000000000000000000000000000000000000000000000000040000000000000"
        + "00000000000000000000000000000000000000000000000000800000000000000000000000"
        + "00000000000000000000000000000000000000000a45564d42616c616e6365000000000000"
        + "00000000000000000000000000000000000000000000000000000000000000000000000000"
        + "00000000000000000000600000000000000000000000000000000000000000000000000000"
        + "000000aa36a7000000000000000000000000210766226c54cdd6bd0401749d43e7a5585e38"
        + "680000000000000000000000000000000000000000000000000000000065b41af5"
    )

    assert q.query_data == exp_abi

    query_type, encoded_param_vals = decode_abi(["string", "bytes"], q.query_data)
    assert query_type == "EVMBalance"

    (chainId, evmAddress, timestamp) = decode_abi(["uint256", "address", "uint256"], encoded_param_vals)

    assert chainId == 11155111
    assert evmAddress == "0x210766226c54cdd6bd0401749d43e7a5585e3868"
    assert timestamp == 1706302197
    assert isinstance(chainId, int)
    assert isinstance(evmAddress, str)
    assert isinstance(timestamp, int)
    assert q.query_id.hex() == "3be82186770410339e9cb0a3d628b7c92ea898a387deaf94906725643f122f86"
