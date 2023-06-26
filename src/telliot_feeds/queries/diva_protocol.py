import logging
from dataclasses import dataclass
from typing import Any
from typing import Optional
from typing import Union

from clamfig import deserialize
from clamfig.base import Registry
from eth_abi import decode_abi
from eth_abi import encode_abi
from eth_utils import to_checksum_address
from hexbytes import HexBytes

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
            Example: "0x2C9c47E7d254e493f02acfB410864b9a86c28e1D"

        chainId:
            Network identifier

            More about this query:
            https://github.com/tellor-io/dataSpecs/blob/main/types/DIVAProtocol.md

            More about Diva Protocol:
            https://divaprotocol.io
    """

    poolId: Optional[HexBytes] = None
    divaDiamond: Optional[Union[str, bytes]] = None
    chainId: Optional[int] = None

    #: ABI used for encoding/decoding parameters
    abi = [
        {
            "type": "bytes32",
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
        if self.poolId is not None:
            self.poolId = HexBytes(self.poolId)

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

    @property
    def query_data(self) -> bytes:
        """Encode the query type and parameters to create the query data."""
        if self.poolId is None or self.divaDiamond is None or self.chainId is None:
            raise ValueError(
                "Missing required parameters: "
                + f"{str(self.poolId)}, {self.divaDiamond}, {self.chainId}"  # type: ignore
            )
        param_types = [p["type"] for p in self.abi]
        encoded_params = encode_abi(param_types, [bytes(self.poolId), self.divaDiamond, self.chainId])

        return encode_abi(["string", "bytes"], [type(self).__name__, encoded_params])

    @staticmethod
    def get_query_from_data(query_data: bytes) -> Any:
        """Recreate an oracle query from the `query_data` field"""
        try:
            query_type, encoded_param_values = decode_abi(["string", "bytes"], query_data)
        except OverflowError:
            logger.error("OverflowError while decoding query data.")
            return None
        try:
            cls = Registry.registry[query_type]
        except KeyError:
            logger.error(f"Unsupported query type: {query_type}")
            return None
        params_abi = cls.abi
        param_names = [p["name"] for p in params_abi]
        param_types = [p["type"] for p in params_abi]
        param_values = list(decode_abi(param_types, encoded_param_values))

        param_values[0] = HexBytes(param_values[0])

        params = dict(zip(param_names, param_values))

        return deserialize({"type": query_type, **params})
