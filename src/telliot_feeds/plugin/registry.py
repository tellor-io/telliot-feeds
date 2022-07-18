from dataclasses import dataclass
from dataclasses import field
from typing import Any
from typing import List
from typing import Type

from telliot_feeds.datafeed import DataFeed
from telliot_feeds.datasource import DataSource
from telliot_feeds.queries.query import OracleQuery


@dataclass
class PluginRegistry:
    """Plugin Registry

    This is the main interface for plugins to register capabilities with Telliot
    """

    # #: List of data feed instances to register with telliot_core
    # feeds: List[DataFeed] = field(default_factory=list)

    #: List of custom query dtypes to register with telliot_core
    query_types: List[Type[OracleQuery]] = field(default_factory=list)

    #: List of custom data feed dtypes to register with telliot_core
    feed_types: List[Type[DataFeed[Any]]] = field(default_factory=list)

    #: List of custom data feed dtypes to register with telliot_core
    source_types: List[Type[DataSource[Any]]] = field(default_factory=list)

    # def register_feed(self, feed: DataFeed) -> None:
    #     """Register a feed"""
    #     self.feeds.append(feed)

    def register_query_type(self, query_type: Type[OracleQuery]) -> None:
        """Register a query_type"""
        self.query_types.append(query_type)

    def register_feed_type(self, feed_type: Type[DataFeed[Any]]) -> None:
        """Register a feed type"""
        self.feed_types.append(feed_type)

    def register_source_type(self, feed_type: Type[DataSource[Any]]) -> None:
        """Register a source type"""
        self.source_types.append(feed_type)
