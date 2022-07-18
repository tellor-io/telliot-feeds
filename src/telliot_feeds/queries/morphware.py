import logging
from dataclasses import dataclass

from telliot_feeds.dtypes.value_type import ValueType
from telliot_feeds.queries.abi_query import AbiQuery

logger = logging.getLogger(__name__)


@dataclass
class Morphware(AbiQuery):
    """Returns the result for a given Morphware query version number.

    Attributes:
        version:
            A reference to Morphware data specifications found
            here: www.TODObyMorphware.org/path/to/data/specs

            More about this query:
            https://github.com/tellor-io/dataSpecs/blob/main/types/Morphware.md

            More about Morphware:
            https://morphware.org
    """

    version: int

    #: ABI used for encoding/decoding parameters
    abi = [{"name": "version", "type": "uint256"}]

    @property
    def value_type(self) -> ValueType:
        """Data type returned for a Morphware query.

        - `string[]`: Array containing JSON strings of Ec2Metadata objects.
                    Interface Ec2MetaData {
                        "Instance Type": str,
                        "CUDA Cores": int,
                        "Number of CPUs": int,
                        "RAM": float,
                        "On-demand Price per Hour": float,
                    }
                    Examples of this data type can be found in the tests for
                    this query: tests/test_query_morphware.py
        - `packed`: false
        """
        return ValueType(abi_type="string[]", packed=False)
