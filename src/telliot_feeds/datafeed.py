""" telliot_feeds.datafeed.data_feed

"""
from dataclasses import dataclass
from typing import Generic
from typing import TypeVar

from telliot_core.model.base import Base

from telliot_feeds.datasource import DataSource
from telliot_feeds.queries.query import OracleQuery

T = TypeVar("T")


@dataclass
class DataFeed(Generic[T], Base):
    """Data feed providing query response

    A data feed contains a DataSource to fetch values in response to an `OracleQuery`.

    Attributes:
        query: The Query that this feed responds to
        source: Data source for feed
    """

    query: OracleQuery

    source: DataSource[T]
