import logging
from dataclasses import dataclass
from typing import Optional

from eth_abi import decode_abi
from eth_abi import encode_abi

from telliot_feeds.dtypes.value_type import ValueType
from telliot_feeds.queries.abi_query import AbiQuery

logger = logging.getLogger(__name__)


@dataclass
class BTCBalanceCurrentReturnType(ValueType):

    abi_type: str = "(uint256, uint256)"

    def encode(self, value: list[int]) -> bytes:
        """An encoder for BTCBalanceCurrent response type

        Encodes a tuple of int values.
        """
        if len(value) != 2 or not isinstance(value[0], int) or not isinstance(value[1], int):
            raise ValueError("Invalid response type")

        return encode_abi(["uint256", "uint256"], [int(v) for v in value])

    def decode(self, bytes_val: bytes) -> list[int]:
        """A decoder for BTCBalanceCurrent response type

        Decodes a tuple of int values.
        """
        decoded_tuple = decode_abi(["uint256", "uint256"], bytes_val)
        return list(decoded_tuple)


@dataclass
class BTCBalanceCurrent(AbiQuery):
    """Returns the current BTC balance of a given address.

    More info: https://github.com/tellor-io/dataSpecs/blob/main/types/BTCBalanceCurrent.md

    Attributes:
        btcAddress: the address of the bitcoin hodler
    """

    btcAddress: Optional[str] = None

    #: ABI used for encoding/decoding parameters
    abi = [{"name": "btcAddress", "type": "string"}]

    @property
    def value_type(self) -> ValueType:
        """Data type returned for a BTCBalance query.
        balance
            - 'uint256': balance btc to 18 decimal places
            - 'packed': false
        timestamp
            - 'uint256': block timestamp
            - 'packed': false
        """

        return BTCBalanceCurrentReturnType(abi_type="uint256, uint256", packed=False)
