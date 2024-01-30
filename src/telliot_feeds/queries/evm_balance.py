from dataclasses import dataclass
from typing import Optional

from telliot_feeds.dtypes.value_type import ValueType
from telliot_feeds.queries.abi_query import AbiQuery


@dataclass
class EVMBalance(AbiQuery):
    """Returns the native evm token balance of a given address at a specific timestamp.

    More info: https://github.com/tellor-io/dataSpecs/blob/main/types/EVMBalance.md

    Attributes:
        chainId: the chain id of the relevant evm network
        evmAddress: the address of the hodler
        timestamp: timestamp which will be rounded down to the closest evm chain block
    """

    chainId: Optional[int] = None
    evmAddress: Optional[str] = None
    timestamp: Optional[int] = None

    #: ABI used for encoding/decoding parameters
    abi = [
        {"name": "chainId", "type": "uint256"},
        {"name": "evmAddress", "type": "address"},
        {"name": "timestamp", "type": "uint256"},
    ]

    @property
    def value_type(self) -> ValueType:
        """Data type returned for a EVMBalance query.

        - 'uint256': balance in wei
        - 'packed': false
        """

        return ValueType(abi_type="uint256", packed=False)
