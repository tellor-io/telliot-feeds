"""
Subclass AbiQuery to implement the EVMCall query type.
"""
from dataclasses import dataclass
from typing import Optional

from telliot_feeds.dtypes.value_type import ValueType
from telliot_feeds.queries.abi_query import AbiQuery


@dataclass
class EVMCall(AbiQuery):
    """EVMCall query type.

    More info: https://github.com/tellor-io/dataSpecs/blob/main/types/EVMCall.md

    Parameters
    ----------
    chainId: The chain ID of the network the contract is deployed on
    contractAddress: The address of the contract on the network(e.g. 0x...)
    calldata: The encoding of the function selector and function argument values
    """

    chainId: Optional[int] = None
    contractAddress: Optional[str] = None
    calldata: Optional[bytes] = None

    abi = [
        {"type": "uint256", "name": "chainId"},
        {"type": "address", "name": "contractAddress"},
        {"type": "bytes", "name": "calldata"},
    ]

    @property
    def value_type(self) -> ValueType:
        """Expected response type.

        `bytes` - the encoded value and timestamp
        """
        return ValueType(abi_type="(bytes,uint256)", packed=False)
