import logging
from dataclasses import dataclass
from typing import Optional

from telliot_feeds.dtypes.value_type import ValueType
from telliot_feeds.queries.abi_query import AbiQuery

logger = logging.getLogger(__name__)


@dataclass
class Snapshot(AbiQuery):
    """Returns the proposal result for a given proposal id (an IPFS hash for a certain proposal) coming from Snapshot.
       A boolean value indicating whether a proposal succeeded (True) or failed (False) should be returned.

    Attributes:
        proposal_id:
            Specifies the requested data a of a valid proposal on Snapshot.

    See https://snapshot.org/ for proposal results.
    See the data spec for more info about this query type:
    https://github.com/tellor-io/dataSpecs/blob/main/types/Snapshot.md
    """

    proposalId: Optional[str]

    #: ABI used for encoding/decoding parameters
    abi = [{"name": "proposalId", "type": "string"}]

    @property
    def value_type(self) -> ValueType:
        """Data type returned for a Snapshot query.

        - `bool`: a boolean value true or false equivalent to uint8 restricted to the values 0 and 1
        - `packed`: false
        """

        return ValueType(abi_type="bool", packed=False)
