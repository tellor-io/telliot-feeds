""" :mod:`telliot_feeds.queries.value_type`

"""
from dataclasses import dataclass
from typing import Any

from clamfig import Serializable
from eth_abi.abi import decode_single
from eth_abi.abi import encode_single
from eth_abi.packed import encode_single_packed


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
