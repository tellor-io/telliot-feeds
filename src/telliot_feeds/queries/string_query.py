""" :mod:`telliot_feeds.queries.string_query`

"""
# Copyright (c) 2021-, Tellor Development Community
# Distributed under the terms of the MIT License.
from dataclasses import dataclass
from typing import Optional

from telliot_feeds.dtypes.value_type import ValueType
from telliot_feeds.queries.abi_query import AbiQuery


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
    def value_type(self) -> ValueType:
        """Returns a default text response type."""
        return ValueType(abi_type="string", packed=False)
