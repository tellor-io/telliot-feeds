from dataclasses import dataclass

from telliot_core.dtypes.value_type import ValueType
from telliot_core.queries.abi_query import AbiQuery


@dataclass
class APIQuery(AbiQuery):
    """Returns the output of an API.

    Attributes:
        url:
            url of api to call to get the data
        key_str:
            Names of the values in the returned JSON dict to be returned (comma separated string)

    """

    url: str
    key_str: str

    def __init__(self, url: str, key_str: str):
        self.url = url
        self.key_str = key_str

    #: ABI used for encoding/decoding parameters
    abi = [{"name": "url", "type": "string"}, {"name": "key_str", "type": "string"}]

    @property
    def value_type(self) -> ValueType:
        """
        Data type returned for api query.

        - string containing entire response
        """
        return ValueType(abi_type="string", packed=False)
