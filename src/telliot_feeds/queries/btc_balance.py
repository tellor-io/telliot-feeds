from dataclasses import dataclass
from typing import Optional

from telliot_feeds.dtypes.value_type import ValueType
from telliot_feeds.queries.abi_query import AbiQuery


@dataclass
class BTCBalance(AbiQuery):
    """Returns the BTC balance of a given address at a specific timestamp.

    More info: https://github.com/tellor-io/dataSpecs/blob/main/types/BTCBalance.md

    Attributes:
        btcAddress: the address of the bitcoin hodler
        timestamp: timestamp which will be rounded down to the closest Bitcoin block
    """

    btcAddress: Optional[str] = None
    timestamp: Optional[int] = None

    #: ABI used for encoding/decoding parameters
    abi = [{"name": "btcAddress", "type": "string"}, {"name": "timestamp", "type": "uint256"}]

    @property
    def value_type(self) -> ValueType:
        """Data type returned for a BTCBalance query.

        - 'uint256': balance in btc to 18 decimal places
        - 'packed': false
        """

        return ValueType(abi_type="uint256", packed=False)
