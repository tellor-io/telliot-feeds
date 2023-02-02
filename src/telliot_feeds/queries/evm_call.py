"""
Subclass AbiQuery to implement the EVMCall query type.
"""
from dataclasses import dataclass

from telliot_feeds.queries.abi_query import AbiQuery
from telliot_feeds.dtypes.value_type import ValueType


@dataclass
class EVMCall(AbiQuery):
    """EVMCall query type.

    More info: https://github.com/tellor-io/dataSpecs/blob/main/types/EVMCall.md

    Parameters
    ----------
    chainId: The chain id of the network the contract is deployed on
    contractAddress: The address of the contract on the network(e.g. 0x...)
    calldata: The encoding of the function name and its arguments
    """

    chainId: int
    contractAddress: str
    calldata: str

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
        return ValueType(abi_type="bytes", packed=False)
