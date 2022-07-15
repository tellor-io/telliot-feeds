""" telliot_feeds.datafeed.data_source

"""
import random
from collections import deque
from dataclasses import dataclass
from dataclasses import field
from typing import Deque
from typing import Generic
from typing import List
from typing import TypeVar

from telliot_core.model.base import Base

from telliot_feeds.dtypes.datapoint import DataPoint
from telliot_feeds.dtypes.datapoint import datetime_now_utc
from telliot_feeds.dtypes.datapoint import OptionalDataPoint

T = TypeVar("T")


@dataclass
class DataSource(Generic[T], Base):
    """Base Class for a DataSource

    A DataSource provides an input to a `DataFeed`
    It also contains a store for all previously fetched data points.

    All subclasses must implement `DataSource.fetch_new_datapoint()`
    """

    max_datapoints: int = 256

    # Private storage for fetched values
    _history: Deque[DataPoint[T]] = field(default_factory=deque, init=False, repr=False)

    def __post_init__(self) -> None:
        # Overwrite default deque
        self._history = deque(maxlen=self.max_datapoints)

    @property
    def latest(self) -> OptionalDataPoint[T]:
        """Returns the most recent datapoint or none if history is empty"""
        if len(self._history) >= 1:
            return self._history[-1]
        else:
            return None, None

    def store_datapoint(self, datapoint: DataPoint[T]) -> None:
        """Store a datapoint"""
        v, t = datapoint
        if v is not None and t is not None:
            self._history.append(datapoint)

    def get_all_datapoints(self) -> List[DataPoint[T]]:
        """Get a list of all available data points"""
        return list(self._history)

    async def fetch_new_datapoint(self) -> OptionalDataPoint[T]:
        """Fetch new value and store it for later retrieval"""
        raise NotImplementedError

    @property
    def depth(self) -> int:
        return len(self._history)


@dataclass
class RandomSource(DataSource[float]):
    """A random data source

    Returns a random floating point number in the range [0.0, 1.0).
    """

    async def fetch_new_datapoint(self) -> DataPoint[float]:
        fetched_value = random.random()
        timestamp = datetime_now_utc()
        datapoint = (fetched_value, timestamp)

        self.store_datapoint(datapoint)

        return datapoint


# class ConstantSource(DataSource):
#     """A simple data source that fetches a constant value"""
#
#     #: Descriptive name
#     name: str = "Constant"
#
#     #: Constant value
#     constant_value: float
#
#     def __init__(self, value: float, **kwargs: Any):
#         super().__init__(constant_value=value, **kwargs)
#
#     async def update_value(self):
#         return self.value
#
