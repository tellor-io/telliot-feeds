from typing import List

from telliot_core.tellor.tellorflex.autopay import TellorFlexAutopayContract
from telliot_core.utils.timestamp import TimeStamp

from telliot_feeds.reporters.tips.listener.dtypes import QueryIdandFeedDetails
from telliot_feeds.reporters.tips.listener.funded_feeds_filter import FundedFeedFilter
from telliot_feeds.reporters.tips.listener.utils import sort_by_max_tip
from telliot_feeds.reporters.tips.selected_queryid.selected_queryid_multicall_autopay import AutopayMulticall
from telliot_feeds.utils.log import get_logger

logger = get_logger(__name__)
call = AutopayMulticall()
filtr = FundedFeedFilter()


async def fetch_feed_tip(
    autopay: TellorFlexAutopayContract, query_id: bytes, timestamp: TimeStamp = TimeStamp.now().ts
) -> int:
    """Fetch tip amount for a query id"""
    call.autopay = autopay
    month_old = int(timestamp - 2_592_000)
    tip_amount: int = 0

    # get tip amount for one time tip if available
    one_time_tip, status = await autopay.get_current_tip(query_id=query_id)

    if status.ok:
        tip_amount += one_time_tip

    # make the first batch call of getCurrentFeeds, getDataBefore, getTimestampbyQueryIdandIndex
    results, status = await call.currentfeeds_databefore_timestampindexnow_timestampindexold(
        query_id=query_id, now_timestamp=timestamp, month_old_timestamp=month_old
    )
    print(results, "batch_one_response")
    if not status.ok:
        return tip_amount

    # get query id timestamps list and feed ids datafeed
    timestamps_list_and_datafeed, status = await call.timestamp_datafeed(results)

    if not status.ok:
        return tip_amount
    print(timestamps_list_and_datafeed, "batch_two_response")

    # filter out uneligible feeds
    eligible_feeds = await filtr.filter_uneligible_feeds(timestamps_list_and_datafeed, timestamp)

    if not eligible_feeds:
        logger.info("All feeds filtered out current timestamp not eligible for feed tip")
        return tip_amount
    # filter out query id timestamps not eligible for tip
    feeds_with_timestamps_filtered = filtr.timestamps_filter(eligible_feeds)

    unclaimed_count, status = await call.rewards_claimed_status_call(feeds_with_timestamps_filtered)

    if not unclaimed_count:
        tip_amount += tip(feeds_with_timestamps_filtered)
        return tip_amount

    feeds_with_tips = filtr.get_real_balance(feeds_with_timestamps_filtered, unclaimed_count)

    if not feeds_with_tips:
        return tip_amount

    tip_amount += tip(feeds_with_tips)

    return tip_amount


def tip(feeds: List[QueryIdandFeedDetails]) -> int:
    tips = {}

    for feed in feeds:
        query_id = feed.query_id
        if query_id not in tips:
            tips[query_id] = feed.params.reward
        else:
            tips[query_id] += feed.params.reward
    tip_amount = sort_by_max_tip(tips)[0][1]
    return tip_amount
