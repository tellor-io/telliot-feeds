import logging
from dataclasses import dataclass

from telliot_feeds.dtypes.float_type import UnsignedFloatType
from telliot_feeds.dtypes.value_type import ValueType
from telliot_feeds.queries.abi_query import AbiQuery


logger = logging.getLogger(__name__)


@dataclass
class CustomPrice(AbiQuery):
    """Returns the price of a non-crypto asset like a stock,
    derivatives product, or legacy market commodity.
    More info: https://github.com/tellor-io/dataSpecs/blob/main/types/CustomPrice.md

    Attributes:
        - identifier: Context ID (e.g. StockPrice), provides context for the data.
        - asset: Asset ID (e.g. NVDA)
        - currency: Currency (e.g. USD)
        - unit: Unit of measurement (e.g.for commodities: bushel, ounce, megatonne)
        Note: The unit is optional for if not required.
    """

    identifier: str
    asset: str
    currency: str
    unit: str

    #: ABI used for encoding/decoding parameters
    abi = [
        {"name": "identifier", "type": "string"},
        {"name": "asset", "type": "string"},
        {"name": "currency", "type": "string"},
        {"name": "unit", "type": "string"},
    ]

    @property
    def value_type(self) -> ValueType:
        """Data type returned for a CustomPrice query.

        - `ufixed256x18`: 256-bit unsigned integer with 18 decimals of precision
        - `packed`: false
        """
        return UnsignedFloatType(abi_type="ufixed256x18", packed=False)
