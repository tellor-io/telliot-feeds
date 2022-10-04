""" :mod:`telliot_feeds.queries.price_query`

"""
import logging
from dataclasses import dataclass

from telliot_feeds.dtypes.float_type import UnsignedFloatType
from telliot_feeds.dtypes.value_type import ValueType
from telliot_feeds.queries.abi_query import AbiQuery


logger = logging.getLogger(__name__)


@dataclass
class AmpleforthCustomSpotPrice(AbiQuery):
    """Returns VWAP for AMPL in USD.

    More details in the data spec: https://github.com/tellor-io/dataSpecs/blob/master/AmpleforthCustomSpotPrice.md
    """

    @property
    def value_type(self) -> ValueType:
        """Data type returned for a SpotPrice query.

        - `ufixed256x18`: 256-bit unsigned integer with 18 decimals of precision
        - `packed`: false
        """
        return UnsignedFloatType(abi_type="ufixed256x18", packed=False)
