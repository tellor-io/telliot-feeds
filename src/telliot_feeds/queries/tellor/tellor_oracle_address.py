import logging
from dataclasses import dataclass

from telliot_feeds.dtypes.value_type import ValueType
from telliot_feeds.queries.abi_query import AbiQuery

logger = logging.getLogger(__name__)


@dataclass
class TellorOracleAddress(AbiQuery):
    """Returns the latest Tellor oracle address.
    It is used for updating the time based rewards recipient on Ethereum mainnet.

    Attributes:
        phantom:
            Empty bytes, always used for query types with no arguments

    See the data spec for more info about this query type:
    https://github.com/tellor-io/dataSpecs/blob/main/types/TellorOracleAddress.md
    """

    @property
    def value_type(self) -> ValueType:
        """Data type returned for a TellorOracleAddress query.

        - `address`: the address of the Tellor oracle
        - `packed`: false
        """

        return ValueType(abi_type="address", packed=False)
