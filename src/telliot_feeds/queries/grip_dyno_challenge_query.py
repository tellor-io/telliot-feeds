import logging
from dataclasses import dataclass
from typing import Any
from typing import Optional

from clamfig import deserialize
from clamfig.base import Registry
from eth_abi import decode_abi
from eth_abi import encode_abi
from hexbytes import HexBytes

from telliot_feeds.dtypes.value_type import ValueType
from telliot_feeds.queries.abi_query import AbiQuery


logger = logging.getLogger(__name__)


@dataclass
class GripDynoReturnType(ValueType):

    abi_type: str = "(bool,uint256,uint256,string,string,uint256)"

    def encode(self, value: list[Any]) -> bytes:
        """encoder for grip dyno challenge response type

        Encodes a tuple of 6 values.
        """
        # check types
        return encode_abi(
            ["bool", "uint256", "uint256", "string", "string", "uint256"],
            [
                value[0],  # bool
                int(value[1]),  # uint256
                int(value[2]),  # uint256
                value[3],  # string
                value[4],  # string
                int(value[5]),  # uint256
            ],
        )

    def decode(self, bytes_val: bytes) -> tuple[Any, ...]:
        """A decoder for grip dyno challenge response type

        Decodes a tuple of 6 values.
        """
        return decode_abi(["bool", "uint256", "uint256", "string", "string", "uint256"], bytes_val)


@dataclass
class EthDenverChallenge2025(AbiQuery):
    """Returns the self-reported results of an in person grip strength dynometer challenge.
    Attributes:
        challengeType:
            descriptor for the challenge
            Example: "grip_strength_dynometer"
    """

    challengeType: Optional[str]

    def __init__(self, challengeType: Optional[str]):

        self.challengeType = challengeType

    #: ABI used for encoding/decoding parameters
    abi = [
        {
            "name": "challengeType",
            "type": "string",
        },
    ]

    @property
    def value_type(self) -> GripDynoReturnType:
        """Return the value type for this query."""
        return GripDynoReturnType()

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
