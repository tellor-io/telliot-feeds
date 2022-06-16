""" telliot_core.datafeed.data_feed

"""
from dataclasses import dataclass
from typing import Generic
from typing import TypeVar

from telliot_core.datasource import DataSource
from telliot_core.model.base import Base
from telliot_core.queries.query import OracleQuery

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


if __name__ == "__main__":
    # Example:
    from telliot_core.datasource import RandomSource
    from telliot_core.queries.legacy_query import LegacyRequest

    feed = DataFeed(source=RandomSource(), query=LegacyRequest(legacy_id=99))

    import yaml

    print(yaml.dump(feed.get_state(), sort_keys=False))
