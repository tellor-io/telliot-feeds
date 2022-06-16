""" :mod:`telliot_core.queries.price_query`

"""
import json
import logging
from dataclasses import dataclass
from typing import List
from typing import Tuple

from telliot_core.dtypes.float_type import UnsignedFloatType
from telliot_core.dtypes.value_type import ValueType
from telliot_core.queries.abi_query import AbiQuery

from telliot_feed_examples.utils.home import TELLIOT_FEEDS_ROOT

logger = logging.getLogger(__name__)

currencies = ["usd", "jpy", "eth"]


def get_spot_price_pairs() -> List[Tuple[str, str]]:
    """Read the list of valid spot price pairs"""
    data = TELLIOT_FEEDS_ROOT / "data" / "spot_price_pairs.json"

    with open(data) as f:
        state = json.load(f)

    pairs = []
    for s in state:
        asset_id, currency = s.split("/")
        pairs.append((asset_id.lower(), currency.lower()))

    return pairs


spot_price_pairs = get_spot_price_pairs()


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

        if self.currency not in currencies:
            raise ValueError(f"currency {self.currency} not supported")

        if (self.asset, self.currency) not in spot_price_pairs:
            raise ValueError(f"{self.asset}/{self.currency} is not a supported pair")
