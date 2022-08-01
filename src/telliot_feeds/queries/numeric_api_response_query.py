from dataclasses import dataclass
from typing import Optional

from telliot_feeds.dtypes.float_type import UnsignedFloatType
from telliot_feeds.dtypes.value_type import ValueType
from telliot_feeds.queries.abi_query import AbiQuery


@dataclass
class NumericApiResponse(AbiQuery):
    """The numeric value from an API response.

    Attributes:
        url:
            url of api to call to get the data
        parseStr:
            Comma-separated string of keys and array indices to access the
            target numerical value in the JSON response returned from the API endpoint
    """

    url: Optional[str]
    parseStr: Optional[str]

    def __init__(self, url: Optional[str], parseStr: Optional[str]):
        self.url = url
        self.parseStr = parseStr

    #: ABI used for encoding/decoding parameters
    abi = [{"name": "url", "type": "string"}, {"name": "parseStr", "type": "string"}]

    @property
    def value_type(self) -> ValueType:
        """Data type returned for a SpotPrice query.

        - `ufixed256x18`: 256-bit unsigned integer with 18 decimals of precision
        - `packed`: false
        """
        return UnsignedFloatType(abi_type="ufixed256x18", packed=False)
