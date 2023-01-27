import logging
from dataclasses import dataclass

from telliot_feeds.dtypes.value_type import ValueType
from telliot_feeds.queries.abi_query import AbiQuery

logger = logging.getLogger(__name__)


@dataclass
class AutopayAddresses(AbiQuery):
    """Returns an array of current Tellor autopay addresses.
    It is used for retrieving user vote weights for disputes in the governance contract.

    Attributes:
        phantom:
            Empty bytes, always used for query types with no arguments

    See the data spec for more info about this query type:
    https://github.com/tellor-io/dataSpecs/blob/main/types/AutopayAddresses.md
    """

    @property
    def value_type(self) -> ValueType:
        """Data type returned for a AutopayAddresses query.

        - `address[]`: the addresses of the Tellor Autopay contracts
        - `packed`: false
        """

        return ValueType(abi_type="address[]", packed=False)
