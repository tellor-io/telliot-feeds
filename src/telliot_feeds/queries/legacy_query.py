""" :mod:`telliot_feeds.queries.legacy_query`

"""
from dataclasses import dataclass

from telliot_feeds.dtypes.float_type import UnsignedFloatType
from telliot_feeds.dtypes.value_type import ValueType
from telliot_feeds.queries.abi_query import AbiQuery


@dataclass
class LegacyRequest(AbiQuery):
    """Legacy Price/Value request

    Legacy request are queries that existed prior to TellorX
    A legacy query uses arbitrary query ``data`` and a static query ``id``.
    The query ``id`` is always set to the legacy request ID, which is
    a static integer less than 100.

    The LegacyQuery class is deprecated and should not be used by
    new projects.

    Refer to [tellor documentation](https://docs.tellor.io/tellor/integration/data-ids)
    for a description of each ``id``

    """

    legacy_id: int

    abi = [{"name": "legacy_id", "type": "uint256"}]

    @property
    def value_type(self) -> ValueType:
        if self.legacy_id in [10, 41]:
            """Returns the Legacy Value Type for AMPL legacy queries"""
            return UnsignedFloatType(abi_type="ufixed256x18", packed=False)
        else:
            """Returns the Legacy Value Type for all other legacy queries"""
            return UnsignedFloatType(abi_type="ufixed256x6", packed=False)

    @property
    def query_id(self) -> bytes:
        """Override query ``id`` with the legacy request ID."""
        return self.legacy_id.to_bytes(32, "big", signed=False)
