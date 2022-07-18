""" Unit tests for Snapshot queries

Copyright (c) 2021-, Tellor Development Community
Distributed under the terms of the MIT License.
"""
from eth_abi import decode_abi

from telliot_feeds.queries.snapshot import Snapshot


def test_constructor():
    """Validate snapshot query."""
    q = Snapshot(proposalId="aDd6cYVvfoKvkDX14jRcN86z6bfV135npUfhxmENjHnQ1")

    exp = (
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x00@\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x80\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08Snapshot\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00 \x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x00-aDd6cYVvfoKvkDX14jRcN86z6bfV135npUfhxmENjHnQ1"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    )

    assert q.query_data == exp

    query_type, encoded_param_vals = decode_abi(["string", "bytes"], q.query_data)
    assert query_type == "Snapshot"

    proposal_id = decode_abi(["string"], encoded_param_vals)[0]
    assert isinstance(proposal_id, str)
    assert proposal_id == "aDd6cYVvfoKvkDX14jRcN86z6bfV135npUfhxmENjHnQ1"

    exp = "8ccceed53f0783c04efe8532b367c16a9ef9132e896f20f7946e38d72decf0a8"
    assert q.query_id.hex() == exp


def test_encode_decode_reported_val():
    """Ensure expected encoding/decoding behavior."""
    q = Snapshot(proposalId="aDd6cYVvfoKvkDX14jRcN86z6bfV135npUfhxmENjHnQ1")

    # a boolean value indicating whether a proposal succeeded (True) or failed (False)
    proposal_result = True

    submit_value = q.value_type.encode(proposal_result)
    assert isinstance(submit_value, bytes)

    decoded_result = q.value_type.decode(submit_value)
    assert isinstance(decoded_result, bool)

    assert decoded_result is True
    assert True

    # q = Snapshot(
    #     proposalId="0xcce9760adea906176940ae5fd05bc007cc9252b524832065800635484cb5cb57"
    # )
    # print("q data", q.query_data.hex())
    # print("q id", q.query_id.hex())
    # rsp = q.value_type.encode(True)
    # print("q response", rsp.hex())
