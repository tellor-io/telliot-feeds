""" Unit tests for modern price queries

Copyright (c) 2021-, Tellor Development Community
Distributed under the terms of the MIT License.
"""
import pytest

from telliot_feeds.queries.price.twap import TWAP


def test_constructor():
    """Validate spot price query"""
    q = TWAP(asset="btc", currency="USD", timespan=86400)

    exp_data_abi = "000000000000000000000000000000000000000000000000000000000000004000000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000004545741500000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000e0000000000000000000000000000000000000000000000000000000000000006000000000000000000000000000000000000000000000000000000000000000a000000000000000000000000000000000000000000000000000000000000151800000000000000000000000000000000000000000000000000000000000000003627463000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000037573640000000000000000000000000000000000000000000000000000000000"  # noqa: E501
    assert q.query_data.hex() == exp_data_abi

    exp = "18043d2ec387f70a62430753cb717e4f0c8a4de5344c75b3cd8bc65147c7c4c6"
    assert q.query_id.hex() == exp


def test_invalid_currency():
    with pytest.raises(ValueError):
        _ = TWAP(asset="btc", currency="xxx", timespan=86400)


def test_invalid_pair():

    with pytest.raises(ValueError):
        _ = TWAP(asset="xxx", currency="usd", timespan=86400)


def test_vsq_usd_twap_price():
    q = TWAP(asset="vsq", currency="usd", timespan=86400)
    assert q.query_id.hex() == "2b717a1b27bcee009f8190a78092c2de595566d5998f7ac18cd9d8efd27e24c0"


def test_bct_usd_twap_price():
    q = TWAP(asset="bct", currency="usd", timespan=86400)
    assert q.query_id.hex() == "7d959edc69b5c9851ce030eb33d3848451b9636f2ec836158c6450309577f100"


def test_encode_decode_reported_val():
    """Ensure expected encoding/decoding behavior."""
    q = TWAP(asset="btc", currency="usd", timespan=86400)

    # JSON string containing data specified and
    # referenced in Tellor /dataSpecs:
    # https://github.com/tellor-io/dataSpecs/blob/main/types/TWAP.md

    data = 12000  # example BTC/USD price

    submit_value = q.value_type.encode(data)
    assert isinstance(submit_value, bytes)

    decoded_data = q.value_type.decode(submit_value)

    assert isinstance(decoded_data, float)

    assert decoded_data == 12000
