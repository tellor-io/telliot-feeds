import logging
from dataclasses import dataclass
from typing import Optional

from telliot_feeds.dtypes.float_type import UnsignedFloatType
from telliot_feeds.queries.abi_query import AbiQuery

logger = logging.getLogger(__name__)


@dataclass
class MimicryCollectionStat(AbiQuery):
    """Returns the result for a given MimicryCollectionStat query.

    Attributes:
        version:
            A reference to MimicryCollectionStat data specifications found
            here:
            https://github.com/tellor-io/dataSpecs/blob/main/types/MimicryCollectionStat.md

            More information about the Mimicry Protocol, visit:
            https://www.mimicry.finance/
    """

    chainId: Optional[int]
    collectionAddress: Optional[str]
    metric: Optional[int]

    #: ABI used for encoding/decoding parameters
    abi = [
        {
            "type": "uint256",
            "name": "chainId",
        },
        {
            "type": "address",
            "name": "collectionAddress",
        },
        {
            "type": "uint256",
            "name": "metric",
        },
    ]

    @property
    def value_type(self) -> UnsignedFloatType:
        """
        Data type returned for a MimicryCollectionStat query.
        Returns the desired metric of the collection address
        on the requested chainId.

        - abi_type: ufixed256x18 (18 decimals of precision)
        - packed: false

        """
        return UnsignedFloatType(abi_type="ufixed256x18", packed=False)
