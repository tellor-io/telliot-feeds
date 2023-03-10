import logging
from dataclasses import dataclass
from typing import Optional

from telliot_feeds.dtypes.float_type import UnsignedFloatType
from telliot_feeds.queries.abi_query import AbiQuery


logger = logging.getLogger(__name__)


@dataclass
class MimicryNFTMarketIndex(AbiQuery):
    """Returns the market capitalization metric derived by summing the top 50 NFT collections'
    sales data on a particular chain

    Attributes:
        chain: Mainnet blockchain name that NFT collections live on (e.g. ethereum, solana, etc.)
        currency: Currency used to calculate the market capitalization (e.g. usd, eth, sol)


    See the data spec for more info about this query type:
    https://github.com/tellor-io/dataSpecs/blob/main/types/MimicryNFTMarketIndex.md
    """

    chain: Optional[str]
    currency: Optional[str]

    #: ABI used for encoding/decoding parameters
    abi = [{"name": "chain", "type": "string"}, {"name": "currency", "type": "string"}]

    @property
    def value_type(self) -> UnsignedFloatType:
        """Data type returned for a MimicryNFTMarketIndex query.
        Represents the market capitalization metric derived
        from the 50 most valuable NFT collections' sales data on a particular chain

        - `ufixed256x18`: unsigned fixed-point number with a precision of 18 decimal places
        - `packed`: false
        """

        return UnsignedFloatType(abi_type="ufixed256x18", packed=False)
