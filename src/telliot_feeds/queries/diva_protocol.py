import logging
from dataclasses import dataclass
from typing import Optional
from typing import Union

from eth_abi import decode_abi
from eth_abi import encode_abi
from eth_utils import to_checksum_address

from telliot_feeds.dtypes.value_type import ValueType
from telliot_feeds.queries.abi_query import AbiQuery


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
class DIVAProtocol(AbiQuery):
    """Returns the result for a given option ID (a specific prediction market),
    contract address (containing the relevant pool), and
    chain id to identify the network.

    Attributes:
        poolId:
            Specifies the requested data a of a valid prediction market that's ready to
            be settled on the Diva Protocol.

        divaDiamond:
            Contract address where the selected pool id exists.
            Example: "0xebBAA31B1Ebd727A1a42e71dC15E304aD8905211"

        chainId:
            Network identifier

            More about this query:
            https://github.com/tellor-io/dataSpecs/blob/main/types/DIVAProtocol.md

            More about Diva Protocol:
            https://divaprotocol.io
    """

    poolId: Optional[int] = None
    divaDiamond: Optional[Union[str, bytes]] = None
    chainId: Optional[int] = None

    #: ABI used for encoding/decoding parameters
    abi = [
        {
            "type": "uint256",
            "name": "poolId",
        },
        {
            "type": "address",
            "name": "divaDiamond",
        },
        {
            "type": "uint256",
            "name": "chainId",
        },
    ]

    def __post_init__(self) -> None:
        """Validate parameters."""
        parameters_set = (
            self.poolId is not None,
            self.divaDiamond is not None,
            self.chainId is not None,
        )
        if all(parameters_set):
            self.divaDiamond = to_checksum_address(self.divaDiamond)  # type: ignore

    @property
    def value_type(self) -> DIVAReturnType:
        """Data type returned for a DIVAProtocol query.

        - `(ufixed256x18,ufixed256x18)`: 2x256-bit unsigned integer with 18 decimals of precision
        - `packed`: false
        """
        return DIVAReturnType(abi_type="(ufixed256x18,ufixed256x18)", packed=False)
