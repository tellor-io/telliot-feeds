""" :mod:`telliot_feeds.queries.price_query`

"""
import logging
from dataclasses import dataclass

from telliot_feeds.dtypes.float_type import UnsignedFloatType
from telliot_feeds.dtypes.value_type import ValueType
from telliot_feeds.queries.abi_query import AbiQuery
from telliot_feeds.queries.price.spot_price import CURRENCIES
from telliot_feeds.queries.price.spot_price import format_spot_price_pairs


logger = logging.getLogger(__name__)


@dataclass
class TWAP(AbiQuery):
    """Returns the spot price of a cryptocurrency asset in the given currency.

    Reference: https://github.com/tellor-io/dataSpecs/blob/main/types/TWAP.md

    Attributes:
        1. asset
            - description: Asset ID (ex: ETH)
            - value type: str
        2. currency
            - description: selected currency (ex: USD)
            - value type: str
        3. timespan
            - description: timespan of TWAP in seconds (ex: 86400 for one day)
            - value type: int
    """

    asset: str
    currency: str
    timespan: int

    #: ABI used for encoding/decoding parameters
    abi = [
        {"name": "asset", "type": "string"},
        {"name": "currency", "type": "string"},
        {"name": "timespan", "type": "uint256"},
    ]

    @property
    def value_type(self) -> ValueType:
        """Data type returned for a TWAP query.

        - `ufixed256x18`: 256-bit unsigned integer with 18 decimals of precision
        - `packed`: false
        """
        return UnsignedFloatType(abi_type="ufixed256x18", packed=False)

    def __post_init__(self) -> None:
        """Validate parameters."""
        self.asset = self.asset.lower()
        self.currency = self.currency.lower()

        if self.currency not in CURRENCIES:
            raise ValueError(f"currency {self.currency} not supported")

        if (self.asset, self.currency) not in format_spot_price_pairs():
            raise ValueError(f"{self.asset}/{self.currency} is not a supported pair")
