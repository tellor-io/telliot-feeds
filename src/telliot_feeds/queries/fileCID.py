# Copyright (c) 2021-, Tellor Development Community
# Distributed under the terms of the MIT License.
from dataclasses import dataclass
from typing import Any
from typing import Optional

from eth_abi import decode
from eth_abi import encode

from telliot_feeds.dtypes.value_type import ValueType
from telliot_feeds.queries.abi_query import AbiQuery


class CIDValueType(ValueType):
    """A ValueType for CID Values."""

    def encode(self, value: str) -> Any:
        """Encode a string value."""
        return encode([self.abi_type], [value])  # type: ignore

    def decode(self, bytes_val: bytes) -> Any:
        """Decode bytes into a string value."""
        return decode([self.abi_type], bytes_val)  # type: ignore


@dataclass
class FileCIDQuery(AbiQuery):
    """
    A query type for IPFS content identifier CIDs
    More info: add link to dataspec
    """

    #: Static url
    url: Optional[str]

    def __init__(self, url: Optional[str]):
        self.url = url

    #: ABI used for encoding/decoding parameters
    abi = [{"name": "url", "type": "string"}]

    @property
    def value_type(self) -> CIDValueType:
        """Returns a datatype for ipfs CIDs."""
        return CIDValueType(abi_type="string", packed=False)
