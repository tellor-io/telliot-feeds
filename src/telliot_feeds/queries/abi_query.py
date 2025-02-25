from typing import ClassVar
from typing import Optional

from clamfig import deserialize
from clamfig.base import Registry
from eth_abi import decode
from eth_abi import encode

from telliot_feeds.queries.query import OracleQuery
from telliot_feeds.utils.log import get_logger


logger = get_logger(__name__)


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
            encoded_params = encode(param_types, param_values)

        # If the query has no real parameters, and only the default "phantom" parameter
        else:
            # By default, the queries with no real parameters have a phantom parameter with
            # a consistent value of empty bytes. The encoding of these empty bytese in
            # Python does not match the encoding in Solidity, so the bytes are generated
            # manually like so:
            left_side = b"\0 ".rjust(32, b"\0")
            right_side = b"\0".rjust(32, b"\0")
            encoded_params = left_side + right_side

        return encode(["string", "bytes"], [type(self).__name__, encoded_params])

    @staticmethod
    def get_query_from_data(query_data: bytes) -> Optional[OracleQuery]:
        """Recreate an oracle query from the `query_data` field"""
        try:
            query_type, encoded_param_values = decode(["string", "bytes"], query_data)
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
        param_values = decode(param_types, encoded_param_values)

        params = dict(zip(param_names, param_values))

        return deserialize({"type": query_type, **params})  # type: ignore
