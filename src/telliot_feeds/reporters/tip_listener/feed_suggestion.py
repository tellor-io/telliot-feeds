from typing import Dict, Tuple
from typing import Optional

from telliot_feeds.reporters.tip_listener.funded_feeds import FundedFeeds
from telliot_feeds.reporters.tip_listener.funded_feeds_filter import FundedFeedFilter
from telliot_feeds.reporters.tip_listener.autopay_multicalls import AutopayMulticalls
from telliot_core.tellor.tellorflex.autopay import TellorFlexAutopayContract
from telliot_feeds.reporters.tip_listener.one_time_tips import OneTimeTips
from telliot_feeds.utils.log import get_logger


logger = get_logger(__name__)


# suggest a feed here not a query tag, because build feed portion
# or check both mappings for type
async def feed_suggestion(autopay: TellorFlexAutopayContract) -> Optional[Tuple[bytes, int]]:
    chain_id = autopay.node.chain_id

    if chain_id in (137, 80001, 69, 1666600000, 1666700000, 421611, 42161):
        assert isinstance(autopay, TellorFlexAutopayContract)

    multi_call = AutopayMulticalls()
    feed_filter = FundedFeedFilter()

    one_time_tips = OneTimeTips(autopay=autopay)
    funded_feeds = FundedFeeds(autopay=autopay, multi_call=multi_call, feed_filter=feed_filter)

    feed_tips = await funded_feeds.get_feed_tips()
    single_tips = await one_time_tips.get_one_time_tip_funded_queries()

    if feed_tips and single_tips:
        # merge autopay tips and get feed with max amount of tip
        combined_dict = {
            key: sum_dict_values(single_tips.get(key), feed_tips.get(key))
            for key in single_tips | feed_tips
        }
        tips_sorted = sort_by_max_tip(combined_dict)  # type: ignore
        return tips_sorted[0]
    elif feed_tips is not None:

        return sort_by_max_tip(feed_tips)[0]
    elif single_tips is not None:

        return sort_by_max_tip(single_tips)[0]
    logger.info("No tips available in autopay")
    return None


def sort_by_max_tip(dict: Dict[bytes, int]) -> list[Tuple[bytes, int]]:
    sorted_lis = sorted(dict.items(), key=lambda item: item[1], reverse=True)
    return sorted_lis


def sum_dict_values(x: Optional[int], y: Optional[int]) -> Optional[int]:
    """Helper function to add values when combining dicts with same key"""
    return sum((num for num in (x, y) if num is not None))
