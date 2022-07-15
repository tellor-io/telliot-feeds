""" Unit tests for response type

Copyright (c) 2021-, Tellor Development Community
Distributed under the terms of the MIT License.
"""
from decimal import Decimal

import pytest
from eth_abi.exceptions import InsufficientDataBytes

from telliot_feeds.dtypes.float_type import UnsignedFloatType
from telliot_feeds.dtypes.value_type import ValueType


def test_fixed_response_type():
    """Demonstrate encoding a fixed value with precision=9"""
    value = Decimal("1.0")
    r1 = ValueType(abi_type="ufixed256x9", packed=False)
    bytes_val = r1.encode(value)
    assert bytes_val.hex() == "000000000000000000000000000000000000000000000000000000003b9aca00"
    int_val = int.from_bytes(bytes_val, "big", signed=False)
    assert int_val == 10**9


def test_dynamic_response_type_unpacked():
    """Demonstrate a complex response to a query"""
    r1 = ValueType(abi_type="(int8,bytes,ufixed32x9,bool[])[2]", packed=False)

    value = ((1, b"abc", 1, (True, True)), (1, b"def", 1, (True, True)))

    bytes_val = r1.encode(value)
    print(bytes_val.hex())

    decoded = r1.decode(bytes_val)

    assert decoded == value


def test_packed_response_type_FAILS():
    """Demonstrate encoding a fixed value with precision=9

    This test demonstrates that a custom decoder is required for
    packed values
    """
    value = Decimal("1.0")
    r1 = ValueType(abi_type="ufixed64x9", packed=True)
    bytes_val = r1.encode(value)
    assert bytes_val.hex() == "000000003b9aca00"
    int_val = int.from_bytes(bytes_val, "big", signed=False)
    assert int_val == 10**9

    with pytest.raises(InsufficientDataBytes):
        decoded = r1.decode(bytes_val)
        print(decoded)


def test_unsigned_float_value():
    f = UnsignedFloatType(abi_type="ufixed64x6")
    assert not f.packed
    assert f.decimals == 6
    # Note encoded value is still 256 bits because packed = False
    assert f.nbits == 64
    print(f.get_state())
    encoded_value = f.encode(99.0000009)
    print(encoded_value.hex())
    assert encoded_value.hex() == "0000000000000000000000000000000000000000000000000000000005e69ec1"

    decoded_value = f.decode(encoded_value)
    assert isinstance(decoded_value, float)
    assert decoded_value == 99.000001
