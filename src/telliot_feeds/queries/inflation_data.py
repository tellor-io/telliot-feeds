"""Abi query for inflation data spec"""
import logging
from dataclasses import dataclass
from typing import Optional

from telliot_feeds.dtypes.float_type import UnsignedFloatType
from telliot_feeds.dtypes.value_type import ValueType
from telliot_feeds.queries.abi_query import AbiQuery


logger = logging.getLogger(__name__)


@dataclass
class InflationData(AbiQuery):
    """
    More info: https://github.com/tellor-io/dataSpecs/blob/main/types/InflationData.md

    Attributes:
        - location: The area of the world where the data was collected (e.g. USA)
        - agency: The acronym for or full name of the agency that collected the data (e.g. BLS)
        - category: The category should describe which basket of goods is used to calculate inflation of (e.g. housing)
        - description: The description should include additional information needed to differentiate the
        data.(e.g. index)
    """

    location: Optional[str] = None
    agency: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None

    #: ABI used for encoding/decoding parameters
    abi = [
        {"name": "location", "type": "string"},
        {"name": "agency", "type": "string"},
        {"name": "category", "type": "string"},
        {"name": "description", "type": "string"},
    ]

    @property
    def value_type(self) -> ValueType:
        """Data type returned for a InflationData query.

        - `ufixed256x18`: 256-bit unsigned integer with 18 decimals of precision
        - `packed`: false
        """
        return UnsignedFloatType(abi_type="ufixed256x18", packed=False)
