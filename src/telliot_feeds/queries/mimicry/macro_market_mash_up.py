import logging
from dataclasses import dataclass
from typing import Optional

from telliot_feeds.dtypes.value_type import ValueType
from telliot_feeds.queries.abi_query import AbiQuery


logger = logging.getLogger(__name__)


@dataclass
class MimicryMacroMarketMashup(AbiQuery):
    """Returns the market cap sum of all assets in USD, rounded to the nearest whole dollar.

    Attributes:
        metric: market cap
        currency: Currency used to calculate the market capitalization (e.g. usd)
        colletctions: list of tuples of (blockchain where NFT is deployed, its contract address)
        tokens: list of tuples of (blockchain where NFT is deployed, lower-case symbol, and its contract address)


    See the data spec for more info about this query type:
    https://github.com/tellor-io/dataSpecs/blob/main/types/MimicryMacroMarketMashup.md
    """

    metric: Optional[str]
    currency: Optional[str]
    collections: Optional[list[tuple[str, str]]]
    tokens: Optional[list[tuple[str, str, str]]]

    #: ABI used for encoding/decoding parameters
    abi = [
        {
            "type": "string",
            "name": "metric",
        },
        {
            "type": "string",
            "name": "currency",
        },
        {
            "type": "(string,address)[]",
            "name": "collections",
        },
        {
            "type": "(string,string,address)[]",
            "name": "tokens",
        },
    ]

    @property
    def value_type(self) -> ValueType:
        """Return should be sum of market cap of all assets in USD, rounded to the nearest whole dollar.

        - `uint256`: an unsigned integer value
        - `packed`: false
        """

        return ValueType(abi_type="uint256", packed=False)
