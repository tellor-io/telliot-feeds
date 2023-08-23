import codecs
from typing import ClassVar
from typing import Optional

import pkg_resources
from clamfig import deserialize
from clamfig.base import Registry
from eth_abi import decode_abi
from eth_abi import encode_abi
from eth_abi.encoding import TextStringEncoder
from eth_abi.utils.numeric import ceil32
from eth_abi.utils.padding import zpad_right

from telliot_feeds.queries.query import OracleQuery
from telliot_feeds.utils.log import get_logger


logger = get_logger(__name__)


"""This is a temporary fix for the bug in eth-abi versions < 4.0.0
when empty strings are encoded extra zeros were being added eth-abi version >= 4.0.0 addresses this issue
but upgrading the package will break the telliot_feeds package due dependency version conflicts"""
version = pkg_resources.get_distribution("eth-abi").version
pkg_version = int(version.split(".")[0])


if pkg_version < 4:

    @classmethod
    def encode(cls, value):  # type: ignore
        cls.validate_value(value)

        value_as_bytes = codecs.encode(value, "utf8")
        value_length = len(value_as_bytes)
        encoded_size = encode_abi(["uint256"], [value_length])
        padded_value = zpad_right(value_as_bytes, ceil32(value_length))
        return encoded_size + padded_value

    TextStringEncoder.encode = encode  # type: ignore


class AbiQuery(OracleQuery):
    """An Oracle Query that uses ABI-encoding to compute the query_data.

    Attributes:
        abi:
            The ABI used for encoding/decoding parameters.
            Each subclass must defind the ABI.
            The ABI is an ordered list, with one entry for each query parameter.
            Each parameter should include a dict with two entries:
                {"name": <parameter name>, "type": <parameter type>}
            Parameter types must be valid solidity ABI type string.
                See https://docs.soliditylang.org/en/develop/types.html for reference.

    """

    abi: ClassVar[list[dict[str, str]]] = []

    @property
    def query_data(self) -> bytes:
        """Encode the query type and parameters to create the query data.

        This method uses ABI encoding to encode the query's parameter values.
        """
        # If the query has parameters
        if self.abi:
            param_values = [getattr(self, p["name"]) for p in self.abi]
            param_types = [p["type"] for p in self.abi]
            encoded_params = encode_abi(param_types, param_values)

        # If the query has no real parameters, and only the default "phantom" parameter
        else:
            # By default, the queries with no real parameters have a phantom parameter with
            # a consistent value of empty bytes. The encoding of these empty bytese in
            # Python does not match the encoding in Solidity, so the bytes are generated
            # manually like so:
            left_side = b"\0 ".rjust(32, b"\0")
            right_side = b"\0".rjust(32, b"\0")
            encoded_params = left_side + right_side

        return encode_abi(["string", "bytes"], [type(self).__name__, encoded_params])

    @staticmethod
    def get_query_from_data(query_data: bytes) -> Optional[OracleQuery]:
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
        param_values = decode_abi(param_types, encoded_param_values)

        params = dict(zip(param_names, param_values))

        return deserialize({"type": query_type, **params})  # type: ignore
