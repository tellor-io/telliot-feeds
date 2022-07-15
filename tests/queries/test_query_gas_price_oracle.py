""" Unit tests for GasPriceOracle queries.

Copyright (c) 2021-, Tellor Development Community
Distributed under the terms of the MIT License.
"""
from eth_abi import decode_abi

from telliot_feeds.queries.gas_price_oracle import GasPriceOracle


def test_query_constructor():
    """Validate GasPriceOracle query."""
    q = GasPriceOracle(chainId=1, timestamp=1650552232)

    exp_query_data = bytes.fromhex(
        "00000000000000000000000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000080000000000000000000000000000000000000000000000000000000000000000e47617350726963654f7261636c65000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000004000000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000062616da8"  # noqa: E501
    )

    assert q.query_data == exp_query_data

    query_type, encoded_param_vals = decode_abi(["string", "bytes"], q.query_data)
    assert query_type == "GasPriceOracle"

    decoded_param_vals = decode_abi(["uint256", "uint256"], encoded_param_vals)

    chainId = decoded_param_vals[0]
    assert isinstance(chainId, int)
    assert chainId == 1

    timestamp = decoded_param_vals[1]
    assert isinstance(timestamp, int)
    assert timestamp == 1650552232

    exp = "b52507ebdd1fb0aaaf645c01700ec11835f46a30f8391ec19e8e26b6c1d55f08"
    assert q.query_id.hex() == exp


def test_encode_decode_reported_val():
    """Ensure expected encoding/decoding behavior."""
    q = GasPriceOracle(chainId=1, timestamp=1650552232)

    # JSON string containing data specified and
    # referenced in Tellor /dataSpecs:
    # https://github.com/tellor-io/dataSpecs/blob/main/types/GasPriceOracle.md

    data = 31.7  # example gas price in gwei

    submit_value = q.value_type.encode(data)
    assert isinstance(submit_value, bytes)

    decoded_data = q.value_type.decode(submit_value)

    assert isinstance(decoded_data, float)

    assert decoded_data == 31.7
