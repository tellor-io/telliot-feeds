""" :mod:`telliot_feeds.queries.price_query`

"""
import logging
from dataclasses import dataclass
from typing import List
from typing import Tuple

from telliot_feeds.dtypes.float_type import UnsignedFloatType
from telliot_feeds.dtypes.value_type import ValueType
from telliot_feeds.queries.abi_query import AbiQuery


logger = logging.getLogger(__name__)

CURRENCIES = ["usd", "jpy", "eth"]
SPOT_PRICE_PAIRS = [
    "ETH/USD",
    "BTC/USD",
    "TRB/USD",
    "OHM/ETH",
    "VSQ/USD",
    "BCT/USD",
    "DAI/USD",
    "RIC/USD",
    "MKR/USD",
    "IDLE/USD",
    "SUSHI/USD",
    "MATIC/USD",
    "USDC/USD",
    "EUR/USD",
    "PLS/USD",
    "ETH/JPY",
    "ALBT/USD",
    "RAI/USD",
]


def format_spot_price_pairs() -> List[Tuple[str, str]]:
    """Read the list of valid spot price pairs"""

    pairs = []
    for s in SPOT_PRICE_PAIRS:
        asset_id, currency = s.split("/")
        pairs.append((asset_id.lower(), currency.lower()))

    return pairs


@dataclass
class SpotPrice(AbiQuery):
    """Returns the spot price of a cryptocurrency asset in the given currency.

    Attributes:
        asset:
            Asset ID (see data specifications for a full list of supported assets)
        currency:
            Currency (default = `usd`)

    """

    asset: str
    currency: str

    #: ABI used for encoding/decoding parameters
    abi = [{"name": "asset", "type": "string"}, {"name": "currency", "type": "string"}]

    @property
    def value_type(self) -> ValueType:
        """Data type returned for a SpotPrice query.

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
