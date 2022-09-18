from collections import defaultdict
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple


def filter_batch_result(data: Dict[Any, Any]) -> defaultdict[Any, List[Any]]:
    """Filter data dictionary with tuple key

    >>> example {(current_value, queryid): 0, (current_timestamp, queryid): 123}
    to {queryid: [0, 123]}

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


def get_sorted_tips(
    feed_tips: Optional[Dict[bytes, int]], onetime_tips: Optional[Dict[bytes, int]]
) -> List[Tuple[bytes, int]]:
    """combine and sort tips"""
    if feed_tips and onetime_tips:
        # merge autopay tips and get feed with max amount of tip
        combined_dict = {key: sum_values(onetime_tips.get(key), feed_tips.get(key)) for key in onetime_tips | feed_tips}
        tips_sorted = sort_by_max_tip(combined_dict)  # type: ignore
        suggestion = tips_sorted
    elif feed_tips is not None:
        suggestion = sort_by_max_tip(feed_tips)
    elif onetime_tips is not None:
        suggestion = sort_by_max_tip(onetime_tips)
    return suggestion


def handler_func(res: Any) -> int:
    return len(list(filter((True).__ne__, res)))
