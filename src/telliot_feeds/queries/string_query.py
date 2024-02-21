""" :mod:`telliot_feeds.queries.string_query`

"""
# Copyright (c) 2021-, Tellor Development Community
# Distributed under the terms of the MIT License.
from dataclasses import dataclass
from typing import Any
from typing import Optional

from eth_abi import decode
from eth_abi import encode

from telliot_feeds.dtypes.value_type import ValueType
from telliot_feeds.queries.abi_query import AbiQuery


class StringQueryValueType(ValueType):
    """A ValueType for string queries."""

    def encode(self, value: str) -> Any:
        """Encode a string value."""
        return encode([self.abi_type], [value])  # type: ignore

    def decode(self, bytes_val: bytes) -> Any:
        """Decode bytes into a string value."""
        return decode([self.abi_type], bytes_val)  # type: ignore


@dataclass
class StringQuery(AbiQuery):
    """Static Oracle Query

    A text query supports a question in the form of an arbitrary
    text.
    """

    #: Static query text
    text: Optional[str]

    def __init__(self, text: Optional[str]):
        self.text = text

    #: ABI used for encoding/decoding parameters
    abi = [{"name": "text", "type": "string"}]

    @property
    def value_type(self) -> StringQueryValueType:
        """Returns a default text response type."""
        return StringQueryValueType()
