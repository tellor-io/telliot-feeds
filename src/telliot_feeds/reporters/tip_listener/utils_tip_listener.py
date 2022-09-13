from collections import defaultdict
from dataclasses import dataclass
from dataclasses import field
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

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
    feedsWithFundingIndex: int


@dataclass
class FullFeedQueryDetails:
    """
    - query_data: bytes
    - feed_id: str
    - query_id: str
    - current_value: bytes
    - current_value_timestamp: int
    - current_value_index: int
    - month_old_index: int
    - queryId_timestamps_list: List[int]
    - feed_details: FeedDetails
    """

    feed_details: FeedDetails
    query_data: bytes
    feed_id: Optional[bytes] = None
    query_id: Optional[bytes] = None
    queryId_timestamps_list: List[TimeStamp] = field(default_factory=list)
    current_value: bytes = b""
    current_value_timestamp: TimeStamp = 0
    current_value_index: int = 0
    month_old_index: int = 0
    current_window_start: TimeStamp = 0

    def __post_init__(self) -> None:
        self.feed_details = FeedDetails(*self.feed_details)


def filter_batch_result(data: Dict[Any, Any]) -> defaultdict[Any, List[Any]]:
    """Filter data dictionary with tuple key

    >>> example {(current_value, queryid): 0, (current_timestamp, queryid): 123}
    to {query: [0, 123]}

    Args:
    - data: dictionary

    Return:
    - dictionary with value of list type
    """
    mapping = defaultdict(list)
    results = defaultdict(list)

    for k in data:
        mapping[k[1]].append(k)
    for query_id in mapping:
        for val in mapping[query_id]:
            value = data[val]
            results[query_id].append(value)

    return results


def sum_values(x: Optional[int], y: Optional[int]) -> Optional[int]:
    """Takes two values and returns sum and handles Nonetype"""
    return sum((num for num in (x, y) if num is not None))


def sort_by_max_tip(dict: Dict[bytes, int]) -> list[Tuple[bytes, int]]:
    """Takes dictionary of int type value and sorts by max value"""
    sorted_lis = sorted(dict.items(), key=lambda item: item[1], reverse=True)
    return sorted_lis


def get_suggestion(
    feed_tips: Optional[Dict[bytes, int]], onetime_tips: Optional[Dict[bytes, int]]
) -> Tuple[bytes, int]:

    if feed_tips and onetime_tips:
        # merge autopay tips and get feed with max amount of tip
        combined_dict = {key: sum_values(onetime_tips.get(key), feed_tips.get(key)) for key in onetime_tips | feed_tips}
        tips_sorted = sort_by_max_tip(combined_dict)  # type: ignore
        suggestion = tips_sorted[0]
    elif feed_tips is not None:
        suggestion = sort_by_max_tip(feed_tips)[0]
    elif onetime_tips is not None:
        suggestion = sort_by_max_tip(onetime_tips)[0]
    return suggestion
