"""Test plugin module"""
import pytest

from telliot_feeds.plugin.discover import telliot_plugins


@pytest.mark.skip("Fix test after plugin move complete")
def test_discovered_plugins():
    # Make sure that default telliot_examples plugin package is registered
    assert "telliot_feeds" in telliot_plugins

    example_plugin = telliot_plugins["telliot_feeds"]

    _ = example_plugin.registry


# def test_plugin_registry():
#     """Test barebones plugin registry interface"""
#
#     class MyQueryType(OracleQuery):
#         pass
#
#
#     myfeed = MyFeedType(query=MyQueryType())
#
#     r = PluginRegistry()
#
#     r.register_query_type(MyQueryType)
#     r.register_feed_type(MyFeedType)
#
#     r.register_feed(myfeed)
#
#     assert myfeed in r.feeds
#     assert MyQueryType in r.query_types
#     assert MyFeedType in r.feed_types
