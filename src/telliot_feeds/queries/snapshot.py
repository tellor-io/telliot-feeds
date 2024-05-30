import logging
from dataclasses import dataclass
from typing import Optional

from telliot_feeds.dtypes.value_type import ValueType
from telliot_feeds.queries.abi_query import AbiQuery

logger = logging.getLogger(__name__)


@dataclass
class Snapshot(AbiQuery):
    """Returns the binary proposal result for a given Snapshot proposal id.
       A boolean value indicating whether a proposal succeeded (True) or failed (False) should be returned.

    Attributes:
        proposal_id:
            Specifies the requested data a of a valid proposal on Snapshot.
        transactionsHash:
            a hashed array of proposed transactions (decoded from tipped / reported queryData for telliot)
        moduleAddress:
            address of the module the proposal is associated with.

    See https://snapshot.org/ for proposal results.
    See the data spec for more info about this query type:
    https://github.com/tellor-io/dataSpecs/blob/main/types/Snapshot.md
    """

    proposalId: Optional[str]
    transactionsHash: Optional[str]
    moduleAddress: Optional[str]

    #: ABI used for encoding/decoding parameters
    abi = [
        {"type": "uint256", "name": "proposalId"},
        {"type": "address", "name": "transactionsHash"},
        {"type": "bytes", "name": "moduleAddress"},
    ]

    @property
    def value_type(self) -> ValueType:
        """Data type returned for a Snapshot query.

        - `bool`: a boolean value equivalent to uint8 restricted to the values 0 and 1
        - `packed`: false
        """

        return ValueType(abi_type="bool", packed=False)
