from typing import Any
from typing import List
from typing import Optional

from telliot_core.tellor.tellorflex.autopay import TellorFlexAutopayContract
from telliot_core.utils.timestamp import TimeStamp

from telliot_feeds.datafeed import DataFeed
from telliot_feeds.reporters.tips.listener.dtypes import QueryIdandFeedDetails
from telliot_feeds.reporters.tips.listener.funded_feeds_filter import FundedFeedFilter
from telliot_feeds.reporters.tips.multicall_functions.multicall_autopay import MulticallAutopay
from telliot_feeds.utils.log import get_logger

logger = get_logger(__name__)
call = MulticallAutopay()
filtr = FundedFeedFilter()


async def fetch_feed_tip(
    autopay: TellorFlexAutopayContract, datafeed: DataFeed[Any], timestamp: Optional[TimeStamp] = None
) -> int:
    """Fetch tip amount for a given query id

    Args:
    - query_id

    Returns: tip amount"""
    if timestamp is None:
        timestamp = TimeStamp.now().ts
    call.autopay = autopay
    month_old = int(timestamp - 2_592_000)
    tip_amount: int = 0

    # get tip amount for one time tip if available
    one_time_tip, status = await autopay.get_current_tip(query_id=datafeed.query.query_id)

    if status.ok:
        tip_amount += one_time_tip

    # make the first batch call of getCurrentFeeds, getDataBefore, getTimestampbyQueryIdandIndex
    results, status = await call.currentfeeds_multiple_values_before(
        datafeed=datafeed, now_timestamp=timestamp, month_old_timestamp=month_old
    )

    if not status.ok or not results:
        return tip_amount

    # get query id timestamps list and feed ids datafeed
    timestamps_list_and_datafeed, status = await call.timestamp_datafeed(results)

    if not status.ok or not timestamps_list_and_datafeed:
        return tip_amount

    # filter out uneligible feeds
    eligible_feeds = await filtr.window_and_priceThreshold_unmet_filter(timestamps_list_and_datafeed, timestamp)

    if not eligible_feeds:
        logger.info("All feeds filtered out current timestamp not eligible for feed tip")
        return tip_amount

    # filter out query id timestamps not eligible for tip
    feeds_with_timestamps_filtered = filtr.filter_historical_submissions(eligible_feeds)

    unclaimed_count, status = await call.rewards_claimed_status_call(feeds_with_timestamps_filtered)

    if not unclaimed_count:
        tip_amount += tip_sum(feeds_with_timestamps_filtered)
        return tip_amount

    feeds_with_tips = filtr.calculate_true_feed_balance(feeds_with_timestamps_filtered, unclaimed_count)

    if not feeds_with_tips:
        return tip_amount

    tip_amount += tip_sum(feeds_with_tips)

    return tip_amount


def tip_sum(feeds: List[QueryIdandFeedDetails]) -> int:
    """Sum up the tip from all the feeds"""
    tip_total = 0

    for feed in feeds:
        if feed.params.balance >= feed.params.reward:
            tip_total += feed.params.reward
    return tip_total
