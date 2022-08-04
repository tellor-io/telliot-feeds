"""  Oracle Query Module

"""
from __future__ import annotations

import json
from typing import Any
from typing import Dict
from typing import Optional

from clamfig import deserialize
from clamfig import Serializable
from web3 import Web3

from telliot_feeds.dtypes.value_type import ValueType


class OracleQuery(Serializable):
    """Oracle Query

    An OracleQuery specifies how to pose a question to the
    Tellor Oracle and how to format/interpret the response.

    The OracleQuery class serves
    as the base class for all Queries, and implements default behaviors.
    Each subclass corresponds to a unique Query Type supported
    by the TellorX network.

    All public attributes of an OracleQuery represent a parameter that can
    be used to customize the query.

    The base class provides:

    - Generation of the query `descriptor` JSON string.
    This string provides a simple platform and language independent
    way to identify a query.

    - Calculation of the `id` field from `query_data`.  This value is used for the
      `TellorX.Oracle.tipQuery()` and `TellorX.Oracle.submitValue()`
      contract calls.

    Subclasses must provide:

    - Encoding of the `descriptor` string to compute the `query_data` attribute,
    which is used for the `data` field of a `TellorX.Oracle.tipQuery()` contract call.

    """

    @property
    def value_type(self) -> ValueType:
        """Returns the ValueType expected by the current Query configuration

        The value type defines required data type/structure of the
        ``value`` submitted to the contract through
        ``TellorX.Oracle.submitValue()``

        This method *must* be implemented by subclasses
        """
        raise NotImplementedError

    @property
    def descriptor(self) -> str:
        """Get the query descriptor string.

        The Query descriptor is a unique string representation of the query, including
        all parameter values.  The string must be in valid JSON format (http://www.json.org).

        """
        state = self.get_state()
        json_str = json.dumps(state, separators=(",", ":"))
        return json_str

    @property
    def query_id(self) -> bytes:
        """Returns the query ``id`` for use with the
        ``TellorX.Oracle.tipQuery()`` and ``TellorX.Oracle.submitValue()``
        contract calls.
        """
        return bytes(Web3.keccak(self.query_data))

    @property
    def query_data(self) -> bytes:
        """Encode the query `descriptor` to create the query `data` field for
        use in the ``TellorX.Oracle.tipQuery()`` contract call.

        This method *must* be implemented by subclasses
        """
        raise NotImplementedError

    @staticmethod
    def get_query_from_data(query_data: bytes) -> Optional[OracleQuery]:
        """Recreate an oracle query from `query_data`"""
        raise NotImplementedError


def query_from_descriptor(descriptor: str) -> OracleQuery:
    """Convert a query descriptor into a query object."""
    state = json.loads(descriptor)
    return query_from_state(state)


def query_from_state(state: Dict[str, Any]) -> OracleQuery:
    """Recreate a query object from it's JSON state."""
    return deserialize(state)  # type: ignore
