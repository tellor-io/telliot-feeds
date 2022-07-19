from telliot_feeds.feeds import CATALOG_FEEDS
from telliot_feeds.queries.query_catalog import query_catalog


def test_supports_all_active_queries():
    """Make sure all current queries have an associated feed that reporters can use."""
    active_q_tags = [q.tag for q in query_catalog.find()]

    for qt in active_q_tags:
        assert qt in CATALOG_FEEDS
