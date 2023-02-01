from telliot_feeds.queries.abi_query import AbiQuery
from telliot_feeds.queries.json_query import JsonQuery
from telliot_feeds.queries.query_catalog import query_catalog


def test_all_query_types_in_catalog():
    """Test that all query types are in the catalog."""
    q_types = set((entry.query_type for entry in query_catalog._entries.values()))
    print("Query types in catalog:", q_types)

    for q in AbiQuery.__subclasses__():
        print("Checking", q.__name__)
        # skip legacy type
        if q.__name__ in (
            "LegacyRequest",
            "FakeQueryType",
            "MimicryCollectionStat",
            "AutopayAddresses",
            "TellorOracleAddress",
        ):
            continue
        assert q.__name__ in q_types

    for q in JsonQuery.__subclasses__():
        print("Checking", q.__name__)
        assert q.__name__ in q_types


def test_gen_all_query_ids():
    """Test that all query IDs can be generated."""
    for q in AbiQuery.__subclasses__():
        print("Checking", q.__name__)
        q.query_id

    for q in JsonQuery.__subclasses__():
        print("Checking", q.__name__)
        q.query_id
