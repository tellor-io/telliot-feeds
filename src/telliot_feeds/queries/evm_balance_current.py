import logging
from dataclasses import dataclass
from typing import Optional

from eth_abi import decode_abi
from eth_abi import encode_abi

from telliot_feeds.dtypes.value_type import ValueType
from telliot_feeds.queries.abi_query import AbiQuery

logger = logging.getLogger(__name__)


@dataclass
class EVMBalanceCurrentReturnType(ValueType):

    abi_type: str = "(uint256, uint256)"

    def encode(self, value: list[int]) -> bytes:
        """An encoder for EVMBalanceCurrent response type

        Encodes a tuple of int values.
        """
        if len(value) != 2 or not isinstance(value[0], int) or not isinstance(value[1], int):
            raise ValueError("Invalid response type")

        return encode_abi(["uint256", "uint256"], [int(v) for v in value])

    def decode(self, bytes_val: bytes) -> list[int]:
        """A decoder for EVMBalanceCurrent response type

        Decodes a tuple of int values.
        """
        decoded_tuple = decode_abi(["uint256", "uint256"], bytes_val)
        return list(decoded_tuple)


@dataclass
class EVMBalanceCurrent(AbiQuery):
    """Returns the current native EVM token balance of a given address and chain id.

    More info: https://github.com/tellor-io/dataSpecs/blob/main/types/EVMBalanceCurrent.md

    Attributes:
        chainId: the chain id of the relevant evm network
        evmAddress: the address of the hodler
    """

    chainId: Optional[int] = None
    evmAddress: Optional[str] = None

    #: ABI used for encoding/decoding parameters
    abi = [{"name": "chainId", "type": "uint256"}, {"name": "evmAddress", "type": "address"}]

    @property
    def value_type(self) -> ValueType:
        """Data type returned for a EVMBalance query.

        balance:
            - 'uint256': balance in wei
            - 'packed': false
        timestamp:
            - 'uint256': block timestamp
            - 'packed': false
        """

        return EVMBalanceCurrentReturnType(abi_type="uint256, uint256", packed=False)
