"""Fetch and filter(based on telliot registry) funded queries from autopay
Make calls forward and fill in FullFeedQueryDetails
"""
from typing import Callable
from typing import Optional

from telliot_core.tellor.tellorflex.autopay import TellorFlexAutopayContract
from telliot_core.utils.response import error_status
from telliot_core.utils.response import ResponseStatus
from telliot_core.utils.timestamp import TimeStamp

from telliot_feeds.reporters.tips.listener.dtypes import FeedDetails
from telliot_feeds.reporters.tips.listener.dtypes import QueryIdandFeedDetails
from telliot_feeds.reporters.tips.listener.funded_feeds_filter import FundedFeedFilter
from telliot_feeds.reporters.tips.multicall_functions.multicall_autopay import MulticallAutopay
from telliot_feeds.utils.log import get_logger


logger = get_logger(__name__)


class FundedFeeds(FundedFeedFilter):
    """Fetch Feeds from autopay and filter"""

    def __init__(
        self, autopay: TellorFlexAutopayContract, multi_call: MulticallAutopay, listener_filter: Callable[[bytes], bool]
    ) -> None:
        self.multi_call = multi_call
        self.listener_filter = listener_filter
        self.autopay = self.multi_call.autopay = autopay

    async def get_funded_feed_queries(self) -> tuple[Optional[list[QueryIdandFeedDetails]], ResponseStatus]:
        """Call getFundedFeedDetails autopay function filter response data

        Return: list of tuples of only feed_details and query data
        that exist in telliot registry
        """
        funded_feeds: list[tuple[FeedDetails, bytes]]
        funded_feeds, status = await self.autopay.read("getFundedFeedDetails")

        if not status.ok or not funded_feeds:
            return None, error_status(note="No funded feeds returned by autopay function call")

        supported_funded_feeds = [
            (feed, query_data) for (feed, query_data) in funded_feeds if self.listener_filter(query_data)
        ]

        if not supported_funded_feeds:
            return None, error_status(note="No funded feeds with telliot support found in autopay")
        # create list of QueryIdFeedIdDetails data type that represents all relevant info about a feed
        # including its corresponding query ids timestamps and current values
        funded_feed_details = [
            QueryIdandFeedDetails(params=FeedDetails(*feed_details), query_data=query_data)
            for feed_details, query_data in supported_funded_feeds
        ]
        return funded_feed_details, ResponseStatus()

    async def filtered_funded_feeds(
        self, now_timestamp: int, month_old_timestamp: int
    ) -> tuple[Optional[list[QueryIdandFeedDetails]], ResponseStatus]:

        telliot_supported_feeds, status = await self.get_funded_feed_queries()

        if not status.ok or not telliot_supported_feeds:
            return None, status

        # assemble both feed id and query id
        for feed in telliot_supported_feeds:
            feed.feed_id, feed.query_id = self.generate_ids(feed)
        # for feeds with price threshold gt zero check if api support
        catalog_supported_feeds = self.api_support_check(telliot_supported_feeds)

        # make the first multicall and get current value, current index, and month old value index
        feeds_with_timestamp_index, status = await self.multi_call.timestamp_index_and_current_values_call(
            feeds=catalog_supported_feeds, month_old_timestamp=month_old_timestamp, now_timestamp=now_timestamp
        )

        if not status.ok:
            return None, status

        # filter out feeds where price threshold is zero but now timestamp not in window
        filtered_feeds_with_timestamp_index = await self.window_and_priceThreshold_unmet_filter(
            feeds_with_timestamp_index, now_timestamp
        )

        if not filtered_feeds_with_timestamp_index:
            msg = "No feeds to report, current time outside of window or priceThreshold unmet"
            return None, error_status(msg)

        # multicall to get all timestamps for a query id in the past month
        feeds_with_timestamps_lis, status = await self.multi_call.timestamps_list_call(
            feeds=filtered_feeds_with_timestamp_index
        )

        # return list of feeds if all query ids never had an oracle report
        if "No getTimestampbyQueryIdandIndex Calls to assemble" in status.error:
            return feeds_with_timestamp_index, ResponseStatus()

        # for each queryids timestamps list remove timestamp that wasn't eligible for tip
        timestamps_list_filtered = self.timestamps_filter(feeds=feeds_with_timestamps_lis)

        # get claim status count for every query ids eligible timestamp
        reward_claimed_status, status = await self.multi_call.rewards_claimed_status_call(
            feeds=timestamps_list_filtered
        )

        if reward_claimed_status is None:
            return timestamps_list_filtered, ResponseStatus()

        funded_feeds = self.calculate_true_feed_balance(
            feeds=timestamps_list_filtered, unclaimed_timestamps_count=reward_claimed_status
        )

        return funded_feeds, ResponseStatus()

    async def querydata_and_tip(self, current_time: TimeStamp) -> Optional[dict[bytes, int]]:
        """Main function that triggers all the calls

        Args:
        - current_time: Timestamp

        Returns: Dictionary
        - key: querydata
        - value: tip amount
        """
        one_month_ago = current_time - 2_592_000

        eligible_funded_feeds, status = await self.filtered_funded_feeds(
            now_timestamp=current_time, month_old_timestamp=one_month_ago
        )
        if not eligible_funded_feeds:
            logger.info(status.error)
            return None
        # dictionary of key: queryData with value: tipAmount
        querydata_and_tip = {}
        for funded_feed in eligible_funded_feeds:
            query_data = funded_feed.query_data
            if query_data not in querydata_and_tip:
                querydata_and_tip[query_data] = funded_feed.params.reward
            else:
                querydata_and_tip[query_data] += funded_feed.params.reward

        return querydata_and_tip
