from eth_abi import decode_abi

from telliot_feeds.queries.evm_call import EVMCall

# from eth_abi import encode_abi


def test_evm_call_constructor():
    """Validate EVMCall query."""
    q = EVMCall(
        chainId=1,
        contractAddress="0x88dF592F8eb5D7Bd38bFeF7dEb0fBc02cf3778a0",
        calldata=b"\x18\x16\x0d\xdd",
    )
    expected_query_data = (
        "000000000000000000000000000000000000000000000000000000000000004"
        "000000000000000000000000000000000000000000000000000000000000000800"
        "00000000000000000000000000000000000000000000000000000000000000745564d43616c6c"
        "00000000000000000000000000000000000000000000000000000000000000000000000000000"
        "00000000000000000000000000000000000600000000000000000000000000000000000000000"
        "00000000000000000000000100000000000000000000000088df592f8eb5d7bd38bfef7deb0fbc02cf3778a"
        "00000000000000000000000000000000000000000000000000000000018160ddd"
    )
    print(q.query_data.hex())

    assert q.query_data.hex() == expected_query_data

    query_type, _ = decode_abi(["string", "bytes"], q.query_data)
    assert query_type == "EVMCall"

    exp_q_id = "f3e89f8229e2a9289d043ebfabd5d59b4f97f1b8bcc7c847eea6430e3160dfc9"
    assert q.query_id.hex() == exp_q_id


# test get query from data
def test_evm_call_get_query_from_data():
    """Test get_query_from_data."""
    q = EVMCall(
        chainId=1,
        contractAddress="0x88dF592F8eb5D7Bd38bFeF7dEb0fBc02cf3778a0",
        calldata=b"\x18\x16\x0d\xdd",
    )
    q2 = EVMCall.get_query_from_data(q.query_data)
    assert q2.query_data == q.query_data
