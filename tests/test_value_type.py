""" Unit tests for response type

Copyright (c) 2021-, Tellor Development Community
Distributed under the terms of the MIT License.
"""
from decimal import Decimal

import pytest
from eth_abi.exceptions import InsufficientDataBytes

from telliot_feeds.dtypes.float_type import UnsignedFloatType
from telliot_feeds.dtypes.value_type import decode_single
from telliot_feeds.dtypes.value_type import encode_single
from telliot_feeds.dtypes.value_type import parse_types_decoding
from telliot_feeds.dtypes.value_type import parse_types_encode
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


def test_simple_uint():
    """Test encoding/decoding for uint256"""
    value = 12345
    encoded = encode_single("uint256", value)
    decoded = decode_single("uint256", encoded)
    assert decoded == value


def test_simple_bool():
    """Test encoding/decoding for bool"""
    value = True
    encoded = encode_single("bool", value)
    decoded = decode_single("bool", encoded)
    assert decoded == value


def test_simple_address():
    """Test encoding/decoding for address"""
    value = "0x88df592f8eb5d7bd38bfef7deb0fbc02cf3778a0"
    encoded = encode_single("address", value)
    decoded = decode_single("address", encoded)
    assert decoded == value


def test_simple_string():
    """Test encoding/decoding for string"""
    value = "Hello, world!"
    encoded = encode_single("string", value)
    decoded = decode_single("string", encoded)
    assert decoded == value


def test_simple_bytes():
    """Test encoding/decoding for bytes"""
    value = bytes.fromhex(
        "00000000000000000000000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000080000000000000000000000000000000000000000000000000000000000000000953706F745072696365000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000C0000000000000000000000000000000000000000000000000000000000000004000000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000003657468000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000037573640000000000000000000000000000000000000000000000000000000000"  # noqa: E501
    )
    encoded = encode_single("bytes", value)
    decoded = decode_single("bytes", encoded)
    assert decoded == value


def test_basic_tuple():
    """Test basic tuple types"""
    value = (
        "SpotPrice",
        bytes.fromhex(
            "00000000000000000000000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000080000000000000000000000000000000000000000000000000000000000000000953706F745072696365000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000C0000000000000000000000000000000000000000000000000000000000000004000000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000003657468000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000037573640000000000000000000000000000000000000000000000000000000000"  # noqa: E501
        ),
    )
    encoded = encode_single("(string,bytes)", value)
    decoded = decode_single("(string,bytes)", encoded)
    assert decoded == value


def test_nested_tuple():
    """Test nested tuple types"""
    nested_value = (True, "0x88df592f8eb5d7bd38bfef7deb0fbc02cf3778a0")
    value = (12345, nested_value)
    encoded = encode_single("(uint256,(bool,address))", value)
    decoded = decode_single("(uint256,(bool,address))", encoded)
    assert decoded == value


def test_uint_array():
    """Test uint256 array"""
    value = [1, 2, 3, 4, 5]
    encoded = encode_single("uint256[]", value)
    decoded = decode_single("uint256[]", encoded)
    assert list(decoded) == value


def test_fixed_array():
    """Test fixed-size array"""
    value = [10, 20, 30]
    encoded = encode_single("uint256[3]", value)
    decoded = decode_single("uint256[3]", encoded)
    assert list(decoded) == value


def test_bool_array():
    """Test boolean array"""
    value = [True, False, True]
    encoded = encode_single("bool[]", value)
    decoded = decode_single("bool[]", encoded)
    assert list(decoded) == value


def test_decode_nested_uints():
    """Test decoding nested uints"""
    value = [(1,), (2,)]
    encoded = encode_single("(uint256)[2]", value)
    decoded = decode_single("(uint256)[2]", encoded)
    assert list(decoded) == value


def test_decode_multi_nested_uints():
    """Test decoding nested uints"""
    value = [(1, 2), (2, 3)]
    encoded = encode_single("(uint256,uint256)[2]", value)
    decoded = decode_single("(uint256,uint256)[2]", encoded)
    assert list(decoded) == value


def test_parse_types_encode_simple():
    """Test parse_types_encode with simple type"""
    types, values = parse_types_encode("uint256", 123)
    assert types == ["uint256"]
    assert values == [123]


def test_parse_types_encode_tuple():
    """Test parse_types_encode with tuple type"""
    types, values = parse_types_encode("(uint256,bool)", (123, True))
    assert types == ["uint256", "bool"]
    assert values == [123, True]


def test_parse_types_decoding_simple():
    """Test parse_types_decoding with simple type"""
    types = parse_types_decoding("uint256")
    assert types == ["uint256"]


def test_parse_types_decoding_tuple():
    """Test parse_types_decoding with tuple type"""
    types = parse_types_decoding("(uint256,bool)")
    assert types == ["uint256", "bool"]


def test_parse_types_decoding_tuple_multiple():
    """Test parse_types_decoding with tuple type"""
    types = parse_types_decoding("(uint256,bool)[2]")
    assert types == ["(uint256,bool)[2]"]
