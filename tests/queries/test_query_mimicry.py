""" Unit tests for MimicryCollectionStat queries.

Copyright (c) 2021-, Tellor Development Community
Distributed under the terms of the MIT License.
"""
from eth_abi import decode_abi

from telliot_feeds.queries.mimicry.collection_stat import MimicryCollectionStat


def test_query_constructor():
    """Validate MimicryCollectionStat query."""
    q = MimicryCollectionStat(chainId=1, collectionAddress="0x495f947276749ce646f68ac8c248420045cb7b5e", metric=1)

    exp_query_data = bytes.fromhex(
        "0000000000000000000000000000000000000000000000000000000000000040000000000000000000000000000000000000000000000000000000000000008000000000000000000000000000000000000000000000000000000000000000154d696d69637279436f6c6c656374696f6e53746174000000000000000000000000000000000000000000000000000000000000000000000000000000000000600000000000000000000000000000000000000000000000000000000000000001000000000000000000000000495f947276749ce646f68ac8c248420045cb7b5e0000000000000000000000000000000000000000000000000000000000000001"  # noqa: E501
    )

    assert q.query_data == exp_query_data

    query_type, encoded_param_vals = decode_abi(["string", "bytes"], q.query_data)
    assert query_type == "MimicryCollectionStat"

    decoded_param_vals = decode_abi(["uint256", "address", "uint256"], encoded_param_vals)

    chainId = decoded_param_vals[0]
    assert isinstance(chainId, int)
    assert chainId == 1

    collection_address = decoded_param_vals[1]
    assert isinstance(collection_address, str)
    assert collection_address == "0x495f947276749ce646f68ac8c248420045cb7b5e"

    exp = "ed3c355d636abb074e55dae46cc187d6a082b2144065fd0a4538a645d3800c12"
    assert q.query_id.hex() == exp


def test_encode_decode_reported_val():
    """Ensure expected encoding/decoding behavior."""
    q = MimicryCollectionStat(chainId=1, collectionAddress="0x495f947276749ce646f68ac8c248420045cb7b5e", metric=0)

    # JSON string containing data specified and
    # referenced in Tellor /dataSpecs:
    # https://github.com/tellor-io/dataSpecs/blob/main/types/MimicryCollectionStat.md

    data = 31.7  # example reported metric

    submit_value = q.value_type.encode(data)
    assert isinstance(submit_value, bytes)

    decoded_data = q.value_type.decode(submit_value)

    assert isinstance(decoded_data, float)

    assert decoded_data == 31.7
