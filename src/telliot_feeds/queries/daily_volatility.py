import logging
from dataclasses import dataclass

from telliot_feeds.dtypes.float_type import UnsignedFloatType
from telliot_feeds.queries.abi_query import AbiQuery

logger = logging.getLogger(__name__)


@dataclass
class DailyVolatility(AbiQuery):
    """Returns the result for a given DailyVolatility query.

    Attributes:
        version:
            A reference to DailyVolatility data specifications found
            here:
            https://github.com/tellor-io/dataSpecs/blob/main/types/DailyVolatility.md

            More information about volatility:
            https://www.investopedia.com/terms/v/volatility.asp
    """

    asset: str
    currency: str
    days: int

    #: ABI used for encoding/decoding parameters
    abi = [
        {
            "type": "string",
            "name": "asset",
        },
        {
            "type": "string",
            "name": "currency",
        },
        {"type": "uint256", "name": "days"},
    ]

    @property
    def value_type(self) -> UnsignedFloatType:
        """Data type returned for a DailyVolatility query. Returns a volitility index in decimals.

        - abi_type: ufixed256x18 (18 decimals of precision)
        - packed: false

        """
        return UnsignedFloatType(abi_type="ufixed256x18", packed=False)

    def __post_init__(self) -> None:
        """Validate parameters."""
        self.asset = self.asset.lower()
        self.currency = self.currency.lower()
