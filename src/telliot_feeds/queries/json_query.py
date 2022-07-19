from telliot_feeds.queries.query import OracleQuery
from telliot_feeds.queries.query import query_from_descriptor


class JsonQuery(OracleQuery):
    """An Oracle Query that uses JSON-encoding to compute the query_data."""

    @property
    def query_data(self) -> bytes:
        """Encode the query `descriptor` to create the query `data` field for
        use in the ``TellorX.Oracle.tipQuery()`` contract call.

        """
        return self.descriptor.encode("utf-8")

    @staticmethod
    def get_query_from_data(query_data: bytes) -> OracleQuery:
        """Recreate an oracle query from `query_data`"""
        descriptor = query_data.decode("utf-8")

        return query_from_descriptor(descriptor)
