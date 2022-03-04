from telliot_core.data.query_catalog import query_catalog

from telliot_feed_examples.feeds import CATALOG_FEEDS


def test_supports_all_active_queries():
    """Make sure all current queries have an associated feed that reporters can use."""
    active_q_tags = [q.tag for q in query_catalog.find()]

    for qt in active_q_tags:

        # Skip AWS spot price bc haven't not sure needed for morphware integration
        if "aws-spot-zone" in qt:
            continue

        assert qt in CATALOG_FEEDS
