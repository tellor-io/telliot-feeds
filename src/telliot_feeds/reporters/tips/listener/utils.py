from typing import Any
from typing import Optional


def sum_values(x: Optional[int], y: Optional[int]) -> int:
    """Takes two values and returns sum and handles Nonetype"""
    return sum((num for num in (x, y) if num is not None))


def sort_by_max_tip(dict: dict[bytes, int]) -> list[tuple[bytes, int]]:
    """Takes dictionary of int type value and sorts by max value"""
    return sorted(dict.items(), key=lambda item: item[1], reverse=True)


def get_sorted_tips(
    feed_tips: Optional[dict[bytes, int]], onetime_tips: Optional[dict[bytes, int]]
) -> list[tuple[bytes, int]]:
    """combine and sort tips"""
    if feed_tips and onetime_tips is None:
        return sort_by_max_tip(feed_tips)
    if onetime_tips and feed_tips is None:
        return sort_by_max_tip(onetime_tips)
    else:
        if feed_tips is not None and onetime_tips is not None:
            # merge autopay tips and get feed with max amount of tip
            combined_dict = {
                key: sum_values(onetime_tips.get(key), feed_tips.get(key)) for key in onetime_tips | feed_tips
            }
        return sort_by_max_tip(combined_dict)


def handler_func(res: Any) -> int:
    """handler function used for multicall response
    takes the list of booleans thats returned and return
    a count of False value

    Args:
    - list of booleans

    Return: count of False values
    """
    return len(list(filter((True).__ne__, res)))
