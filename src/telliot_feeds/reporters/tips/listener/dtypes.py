from dataclasses import dataclass
from dataclasses import field
from typing import List

from telliot_core.utils.timestamp import TimeStamp


@dataclass
class FeedDetails:
    """Data types for feed details contract response"""

    reward: int
    balance: int
    startTime: TimeStamp
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
    - current_value_index: submission index for current query id value
    - current_queryid_value: bytes of current query_id value
    - current_value_timestamp: timestamp of current query_id value
    - month_old_index: submission index for month old query id value
    - queryid_timestamps_list: a list of a query_ids' timestamps
    """

    params: FeedDetails = field(default_factory=tuple)  # type: ignore
    feed_id: bytes = field(default_factory=bytes)
    query_data: bytes = field(default_factory=bytes)
    query_id: bytes = field(default_factory=bytes)
    current_value_index: int = field(default_factory=int)
    current_queryid_value: bytes = field(default_factory=bytes)
    current_value_timestamp: TimeStamp = field(default_factory=int)
    month_old_index: int = field(default_factory=int)
    queryid_timestamps_list: List[TimeStamp] = field(default_factory=list)
