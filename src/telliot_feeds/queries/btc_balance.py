from dataclasses import dataclass

from telliot_feeds.queries.abi_query import AbiQuery
from telliot_feeds.dtypes.value_type import ValueType

@dataclass
class BTCBalance(AbiQuery):
    """Returns the BTC balance of a given address at a specific timestamp.

    Attributes:
        btcAddress: the address of the bitcoin hodler
        timestamp: timestamp which will be rounded down to the closest Bitcoin block
    """

    btcAddress: str
    timestamp: int

    #: ABI used for encoding/decoding parameters
    abi = [{"name": "btcAddress", "type": "string"}, {"name": "timestamp", "type": "uint256"}]

    @property
    def value_type(self) -> ValueType:
        """Data type returned for a BTCBalance query.

        - 'uint256': balance in satoshis
        - 'packed': false
        """

        return ValueType(abi_type="uint256", packed=False)

