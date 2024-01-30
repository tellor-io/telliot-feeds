""" Unit tests for BTCBalance Query

Copyright (c) 2024-, Tellor Development Community
Distributed under the terms of the MIT License.
"""
from eth_abi import decode_abi

from telliot_feeds.queries.btc_balance import BTCBalance


def test_btc_balance_query():
    """Validate btc balance query"""
    q = BTCBalance(
        btcAddress="bc1q06ywseed6sc3x2fafppchefqq8v9cqd0l6vx03",
        timestamp=1706051389,
    )
    assert q.value_type.abi_type == "uint256"
    assert q.value_type.packed is False

    exp_abi = bytes.fromhex(
        "0000000000000000000000000000000000000000000000000000000000000040000000"
        + "0000000000000000000000000000000000000000000000000000000080000000000000"
        + "000000000000000000000000000000000000000000000000000a42544342616c616e636"
        + "50000000000000000000000000000000000000000000000000000000000000000000000"
        + "000000000000000000000000000000000000a0000000000000000000000000000000000"
        + "00000000000000000000000000000400000000000000000000000000000000000000000"
        + "000000000000000065b0473d00000000000000000000000000000000000000000000000"
        + "0000000000000002a626331713036797773656564367363337832666166707063686566"
        + "7171387639637164306c367678303300000000000000000000000000000000000000000000"
    )

    assert q.query_data == exp_abi

    query_type, encoded_param_vals = decode_abi(["string", "bytes"], q.query_data)
    assert query_type == "BTCBalance"

    (btcAddress, timestamp) = decode_abi(["string", "uint256"], encoded_param_vals)

    assert btcAddress == "bc1q06ywseed6sc3x2fafppchefqq8v9cqd0l6vx03"
    assert timestamp == 1706051389
    assert isinstance(btcAddress, str)
    assert isinstance(timestamp, int)
    assert q.query_id.hex() == "8e0130642e4beec47a3c2e59daf498fb2ee4069ec58da4ddb34ebc0ed1c62626"
