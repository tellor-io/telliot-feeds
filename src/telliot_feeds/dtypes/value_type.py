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


def encode_single(abi_type: str, value: Any) -> bytes:
    component_types, values = parse_types_encode(abi_type, value)
    encoded = encode(component_types, values)
    return encoded


def decode_single(abi_type: str, value: bytes) -> Any:
    component_types = parse_types_decoding(abi_type)
    decoded = decode(component_types, value)
    if len(component_types) == 1:
        return decoded[0]
    return decoded


def encode_single_packed(abi_type: str, value: Any) -> bytes:
    component_types, values = parse_types_encode(abi_type, value)
    encoded = encode_packed(component_types, values)
    return encoded


def parse_types_encode(types: str, value: Any) -> tuple[list[str], list[Any]]:
    if (not types.startswith("(") and not types.endswith(")")) or (types.startswith("(") and types.endswith("]")):
        return [types], [value]
    parsed = parse(types)
    component_types = [comp.to_type_str() for comp in parsed.components]
    return component_types, list(value)


def parse_types_decoding(types: str) -> list[str]:
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
