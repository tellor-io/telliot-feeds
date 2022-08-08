from typing import ClassVar
from typing import Optional

from clamfig import deserialize
from clamfig.base import Registry
from eth_abi import decode_abi
from eth_abi import encode_abi

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
        param_values = [getattr(self, p["name"]) for p in self.abi]
        param_types = [p["type"] for p in self.abi]
        encoded_params = encode_abi(param_types, param_values)

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
