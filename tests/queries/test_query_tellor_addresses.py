""" Unit tests for TellorOracleAddress and AutopayAddresses queries

Copyright (c) 2021-, Tellor Development Community
Distributed under the terms of the MIT License.
"""
from eth_abi import decode_abi
from web3 import Web3

from telliot_feeds.queries.tellor.autopay_addresses import AutopayAddresses
from telliot_feeds.queries.tellor.tellor_oracle_address import TellorOracleAddress


def test_autopay_constructor():
    """Validate autopay query."""
    q = AutopayAddresses()

    exp = "0000000000000000000000000000000000000000000000000000000000000040000000000000000000000000000000000000000000000000000000000000008000000000000000000000000000000000000000000000000000000000000000104175746f70617941646472657373657300000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000004000000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501

    assert q.query_data.hex() == exp

    query_type, encoded_param_vals = decode_abi(["string", "bytes"], q.query_data)
    assert query_type == "AutopayAddresses"

    phantom_bytes = decode_abi(["bytes"], encoded_param_vals)[0]
    assert isinstance(phantom_bytes, bytes)
    assert phantom_bytes == b""

    exp = "3ab34a189e35885414ac4e83c5a7faa9d8f03a4d530728ef516d203d91d6309c"
    assert q.query_id.hex() == exp


def test_autopay_encode_decode_reported_val():
    """Ensure expected encoding/decoding behavior."""
    q = AutopayAddresses()

    # an address value indicating the current tellor autopay addresses
    current_autopay_addresses = ["0x9BE9B0CFA89Ea800556C6efbA67b455D336db1D0"]

    submit_value = q.value_type.encode(current_autopay_addresses)
    assert isinstance(submit_value, bytes)

    decoded_result = q.value_type.decode(submit_value)
    assert isinstance(decoded_result, tuple)

    assert Web3.toChecksumAddress(decoded_result[0]) == "0x9BE9B0CFA89Ea800556C6efbA67b455D336db1D0"


def test_oracle_address_constructor():
    """Validate TellorOracleAddress query."""

    q = TellorOracleAddress()

    exp = "00000000000000000000000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000080000000000000000000000000000000000000000000000000000000000000001354656c6c6f724f7261636c654164647265737300000000000000000000000000000000000000000000000000000000000000000000000000000000000000004000000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501

    assert q.query_data.hex() == exp

    query_type, encoded_param_vals = decode_abi(["string", "bytes"], q.query_data)
    assert query_type == "TellorOracleAddress"

    phantom_bytes = decode_abi(["bytes"], encoded_param_vals)[0]
    assert isinstance(phantom_bytes, bytes)
    assert phantom_bytes == b""

    exp = "cf0c5863be1cf3b948a9ff43290f931399765d051a60c3b23a4e098148b1f707"
    assert q.query_id.hex() == exp


def test_oracle_address_encode_decode_reported_val():
    """Ensure expected encoding/decoding behavior."""

    q = TellorOracleAddress()

    # an address value indicating the current tellor autopay addresses
    current_oracle_addresses = "0xB3B662644F8d3138df63D2F43068ea621e2981f9"

    submit_value = q.value_type.encode(current_oracle_addresses)
    assert isinstance(submit_value, bytes)

    decoded_result = q.value_type.decode(submit_value)
    assert isinstance(decoded_result, str)

    assert Web3.toChecksumAddress(decoded_result) == "0xB3B662644F8d3138df63D2F43068ea621e2981f9"
