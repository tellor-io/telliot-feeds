""" :mod:`telliot_feeds.queries.value_type`

"""
from dataclasses import dataclass
from typing import Any

from clamfig import Serializable
from eth_abi.abi import decode
from eth_abi.abi import encode
from eth_abi.grammar import parse
from eth_abi.packed import encode_packed


@dataclass
class ValueType(Serializable):
    """Value Type

    A ValueType specifies the data structure of ``value`` included in
    the ``TellorX.Oracle.submitValue()`` used in response to
    tip request.

    The type is specified per eth-abi grammar, i.e.

    - https://eth-abi.readthedocs.io/en/latest/grammar.html
    """

    # ABI Encoding type string
    abi_type: str = "string"

    #: True if the value should be encoded using packed bytes format.
    packed: bool = False

    def encode(self, value: Any) -> bytes:
        """Encode a value using the ABI Type string."""
        if self.packed:
            return encode_single_packed(self.abi_type, value)
        else:
            return encode_single(self.abi_type, value)

    def decode(self, bytes_val: bytes) -> Any:
        """Decode bytes into a value using abi type string."""
        return decode_single(self.abi_type, bytes_val)


# TODO: Remove the following and use encode throughout the codebase, no some encode_single and some encode
# because this is confusing and decoding could inconsistent since encode_single return a single value
# and encode returns a tuple. mainly helpful in the dvm
def encode_single(abi_type: str, value: Any) -> bytes:
    """Encode a single item field like a tuple string (uint256,bool) or a single type string like uint256"""
    component_types, values = parse_types_encode(abi_type, value)
    encoded = encode(component_types, values)
    return encoded


def decode_single(abi_type: str, value: bytes) -> Any:
    """Decode a single item field like a tuple string (uint256,bool) or a single type string like uint256"""
    component_types = parse_types_decoding(abi_type)
    decoded = decode(component_types, value)
    if len(component_types) == 1:
        return decoded[0]  # unpack if only a single value
    return decoded


def encode_single_packed(abi_type: str, value: Any) -> bytes:
    """Handle packed encoding for single item fields"""
    component_types, values = parse_types_encode(abi_type, value)
    encoded = encode_packed(component_types, values)
    return encoded


def parse_types_encode(types: str, value: Any) -> tuple[list[str], list[Any]]:
    """
    Parse abi types to the proper format to be consumed by eth-abi.encode
        For complex types like multi-nested tuples, cast to a list and return.
        For simple types, parse the types and return a list of types and cast values to a list.
    - For example:
        parse_types_encode("(uint256,bool)", (123, True)) returns (["uint256", "bool"], [123, True])
        parse_types_encode("uint256", 123) returns (["uint256"], [123])
        if types is a nested tuple, ie "(uint256,(bool,address))"
        it will return (["uint256", "(bool,address)"], [123, (True, "0x88df592f8eb5d7bd38bfef7deb0fbc02cf3778a0")])
        or "(uint256)[2]", [[123],[456]] will return ['(uint256,uint256)[2]'] [[[1, 2], [2, 3]]]
    """
    if (not types.startswith("(") and not types.endswith(")")) or (types.startswith("(") and types.endswith("]")):
        return [types], [value]
    parsed = parse(types)
    component_types = [comp.to_type_str() for comp in parsed.components]
    return component_types, list(value)


def parse_types_decoding(types: str) -> list[str]:
    """
    Parse abi types to the proper format to be consumed by eth-abi.decode

    - For example:
        parse_types_decoding("(uint256,bool)") returns ["uint256", "bool"]
        parse_types_decoding("uint256") returns ["uint256"]
        if types is a nested tuple, ie "(uint256,(bool,address))" it will return ["uint256", "(bool,address)"]
        or "(uint256)[2]" will return ["(uint256)[2]"]

    """
    if (not types.startswith("(") and not types.endswith(")")) or (types.startswith("(") and types.endswith("]")):
        return [types]
    parsed = parse(types)
    component_types = [comp.to_type_str() for comp in parsed.components]
    return component_types
    # @validator("abi_type")
    # def require_valid_grammar(cls, v: str) -> str:
    #     """A validator to require well formed ABI type string grammar."""
    #     t = eth_abi.grammar.parse(v)
    #     t.validate()
    #     return eth_abi.grammar.normalize(v)  # type: ignore
    #
    # def json(self, **kwargs: Any) -> str:
    #     """Return compact json format used in query descriptor"""
    #
    #     return super().json(**kwargs, separators=(",", ":"))
