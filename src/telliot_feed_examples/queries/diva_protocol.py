import logging
from dataclasses import dataclass

from eth_abi import decode_abi
from eth_abi import encode_abi

from telliot_core.dtypes.value_type import ValueType
from telliot_core.queries.abi_query import AbiQuery


logger = logging.getLogger(__name__)


@dataclass
class DIVAReturnType(ValueType):

    abi_type: str = "(ufixed256x18,ufixed256x18)"

    def encode(self, value: list[float]) -> bytes:
        """An encoder for DIVA Protocol response type

        Encodes a tuple of float values.
        """
        if len(value) != 2 or not isinstance(value[0], float) or not isinstance(value[1], float):
            raise ValueError("Invalid response type")

        return encode_abi(["uint256", "uint256"], [int(v * 1e18) for v in value])

    def decode(self, bytes_val: bytes) -> list[float]:
        """A decoder for DIVA Protocol response type

        Decodes a tuple of float values.
        """
        return [float(float(v) / 1e18) for v in decode_abi(["uint256", "uint256"], bytes_val)]


@dataclass
class DIVAProtocolPolygon(AbiQuery):
    """Returns the result for a given option ID (a specific prediction market) on the
    Diva Protocol on Polygon.

    Attributes:
        poolId:
            Specifies the requested data a of a valid prediction market that's ready to
            be settled on the Diva Protocol, on the Polygon network.

            More about this query:
            https://github.com/tellor-io/dataSpecs/blob/main/types/DIVAProtocolPolygon.md

            More about Diva Protocol:
            https://divaprotocol.io
    """

    poolId: int

    #: ABI used for encoding/decoding parameters
    abi = [{"name": "poolId", "type": "uint256"}]

    @property
    def value_type(self) -> DIVAReturnType:
        """Data type returned for a DIVAProtocolPolygon query.

        - `ufixed256x18`: 256-bit unsigned integer with 18 decimals of precision
        - `packed`: false
        """
        return DIVAReturnType(abi_type="(ufixed256x18,ufixed256x18)", packed=False)
