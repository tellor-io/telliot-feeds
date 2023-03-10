""" Unit tests for MimicryNFTMarketIndex queries.

Copyright (c) 2021-, Tellor Development Community
Distributed under the terms of the MIT License.
"""
from eth_abi import decode_abi

from telliot_feeds.queries.mimicry.nft_market_index import MimicryNFTMarketIndex

# example data from spec example
# see: https://github.com/tellor-io/dataSpecs/blob/main/types/MimicryNFTMarketIndex.md


q = MimicryNFTMarketIndex(chain="ethereum", currency="usd")


def test_query_constructor():
    """Validate MimicryNFTMarketIndex query."""
    # query data from spec example
    # see: https://github.com/tellor-io/dataSpecs/blob/main/types/MimicryNFTMarketIndex.md
    exp_query_data = bytes.fromhex(
        "0000000000000000000000000000000000000000000000000000000000000040000000000000000000000000000000000000000000000000000000000000008000000000000000000000000000000000000000000000000000000000000000154d696d696372794e46544d61726b6574496e646578000000000000000000000000000000000000000000000000000000000000000000000000000000000000c0000000000000000000000000000000000000000000000000000000000000004000000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000008657468657265756d00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000037573640000000000000000000000000000000000000000000000000000000000"  # noqa: E501
    )
    assert q.query_data == exp_query_data

    query_type, _ = decode_abi(["string", "bytes"], q.query_data)
    assert query_type == "MimicryNFTMarketIndex"

    query: MimicryNFTMarketIndex = q.get_query_from_data(q.query_data)
    assert query.chain == "ethereum"
    assert query.currency == "usd"


def test_encode_decode_reported_val():
    """Ensure expected encoding/decoding behavior."""
    data = 56519.12485  # example reported metric

    submit_value = q.value_type.encode(data)
    assert isinstance(submit_value, bytes)

    decoded_data = q.value_type.decode(submit_value)

    assert isinstance(decoded_data, float)

    assert decoded_data == 56519.12485
