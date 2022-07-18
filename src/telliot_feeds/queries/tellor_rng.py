import logging
from dataclasses import dataclass

from telliot_feeds.dtypes.value_type import ValueType
from telliot_feeds.queries.abi_query import AbiQuery

logger = logging.getLogger(__name__)


@dataclass
class TellorRNG(AbiQuery):
    """Returns a pseudorandom number generated from hashing together blockhashes from multiple chains.

    Attributes:
        timestamp:
            time at which to take the most recent blockhashes (example: 1647624359)
    """

    timestamp: int

    #: ABI used for encoding/decoding parameters
    abi = [{"name": "timestamp", "type": "uint256"}]

    @property
    def value_type(self) -> ValueType:
        """Data type returned for a TellorRNG query.

        - `bytes32`: 32 bytes hexadecimal value
        - `packed`: false
        """
        return ValueType(abi_type="bytes32", packed=False)
