""" Unit tests for BTCBalance Query

Copyright (c) 2024-, Tellor Development Community
Distributed under the terms of the MIT License.
"""
from eth_abi import decode_abi

from telliot_feeds.queries.btc_balance_current import BTCBalanceCurrent


def test_btc_balance_current_query():
    """Validate btc balance query"""
    q = BTCBalanceCurrent(btcAddress="bc1q06ywseed6sc3x2fafppchefqq8v9cqd0l6vx03")
    assert q.value_type.abi_type == "uint256, uint256"
    assert q.value_type.packed is False

    exp_abi = bytes.fromhex(
        "00000000000000000000000000000000000000000000000000000000000000400000000000"
        + "00000000000000000000000000000000000000000000000000008000000000000000000000"
        + "0000000000000000000000000000000000000000001142544342616c616e63654375727265"
        + "6e740000000000000000000000000000000000000000000000000000000000000000000000"
        + "00000000000000000000008000000000000000000000000000000000000000000000000000"
        + "00000000000020000000000000000000000000000000000000000000000000000000000000"
        + "002a6263317130367977736565643673633378326661667070636865667171387639637164"
        + "306c367678303300000000000000000000000000000000000000000000"
    )
    assert q.query_data == exp_abi

    query_type, encoded_param_vals = decode_abi(["string", "bytes"], q.query_data)
    assert query_type == "BTCBalanceCurrent"

    (btcAddress,) = decode_abi(["string"], encoded_param_vals)

    assert btcAddress == "bc1q06ywseed6sc3x2fafppchefqq8v9cqd0l6vx03"
    assert isinstance(btcAddress, str)
    assert q.query_id.hex() == "c699a232e76003b24f9fec5cb319c5cdc8fd0ed1465c7a3e44d0c33cdd854488"
