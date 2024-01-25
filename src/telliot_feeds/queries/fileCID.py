""" :mod:`telliot_feeds.queries.string_query`

"""
# Copyright (c) 2021-, Tellor Development Community
# Distributed under the terms of the MIT License.
from dataclasses import dataclass
from typing import Optional

from telliot_feeds.dtypes.value_type import ValueType
from telliot_feeds.queries.abi_query import AbiQuery


@dataclass
class FileCID(AbiQuery):
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
    def value_type(self) -> ValueType:
        """Returns a datatype for ipfs CIDs."""
        return ValueType(abi_type="string", packed=False)
