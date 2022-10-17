from dataclasses import dataclass
from dataclasses import field


@dataclass
class Values:
    value: bytes
    timestamp: int


@dataclass
class FeedDetails:
    """Data types for feed details contract response"""

    reward: int
    balance: int
    startTime: int
    interval: int
    window: int
    priceThreshold: int
    rewardIncreasePerSecond: int
    feedsWithFundingIndex: int = field(default_factory=int)


@dataclass
class QueryIdandFeedDetails:
    """
    Data types for a query id and feed id contract repsonses details
    - params: parameters from autopay feed details
    - feed_id: hash of feed details
    - query_data: bytes of query
    - query_id: hash of query_data
    - current_queryid_value: bytes of current query_id value
    - current_value_timestamp: timestamp of current query_id value
    - queryid_timestamps_values_list: a list of a query_ids' timestamps and values
    """

    params: FeedDetails = field(default_factory=tuple)  # type: ignore
    feed_id: bytes = field(default_factory=bytes)
    query_data: bytes = field(default_factory=bytes)
    query_id: bytes = field(default_factory=bytes)
    current_queryid_value: bytes = field(default_factory=bytes)
    current_value_timestamp: int = field(default_factory=int)
    queryid_timestamps_values_list: list[Values] = field(default_factory=list)
