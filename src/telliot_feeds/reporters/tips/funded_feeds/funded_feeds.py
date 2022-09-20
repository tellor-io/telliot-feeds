"""Fetch and filter(based on telliot registry) funded queries from autopay
Make calls forward and fill in FullFeedQueryDetails
"""
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

from telliot_core.tellor.tellorflex.autopay import TellorFlexAutopayContract
from telliot_core.utils.response import ResponseStatus
from telliot_core.utils.timestamp import TimeStamp

from telliot_feeds.reporters.tips.funded_feeds.multicall_autopay import MulticallAutopay
from telliot_feeds.reporters.tips.listener.dtypes import FeedDetails
from telliot_feeds.reporters.tips.listener.dtypes import QueryIdandFeedDetails
from telliot_feeds.reporters.tips.listener.funded_feeds_filter import FundedFeedFilter
from telliot_feeds.utils.log import get_logger


logger = get_logger(__name__)


class FundedFeeds:
    """Fetch Feeds from autopay and filter"""

    def __init__(
        self, autopay: TellorFlexAutopayContract, multi_call: MulticallAutopay, feed_filter: FundedFeedFilter
    ) -> None:
        self.multi_call = multi_call
        self.feed_filter = feed_filter
        self.autopay = self.multi_call.autopay = autopay

    async def get_funded_feed_queries(self) -> Tuple[Optional[List[QueryIdandFeedDetails]], ResponseStatus]:
        """Call getFundedFeedDetails autopay function filter response data

        Return: list of tuples of only feed_details and query data
        that exist in telliot registry
        """
        funded_feeds: List[Tuple[FeedDetails, bytes]]
        funded_feeds, status = await self.autopay.read("getFundedFeedDetails")

        if not status.ok or not funded_feeds:
            return None, ResponseStatus(ok=False, error="No funded feeds returned by autopay function call")

        for (details, query_data) in list(funded_feeds):
            # bool response if query type supported by telliot
            if not self.feed_filter.qtype_name_in_registry(query_data):
                funded_feeds.remove((details, query_data))

        if not funded_feeds:
            return None, ResponseStatus(ok=False, error="No funded feeds with telliot support found in autopay")
        # create list of QueryIdFeedIdDetails data type that represents all relevant info about a feed
        # including its corresponding query ids timestamps and current values
        funded_feed_details = [
            QueryIdandFeedDetails(params=FeedDetails(*feed_details), query_data=query_data)
            for feed_details, query_data in funded_feeds
        ]
        return funded_feed_details, ResponseStatus()

    async def filtered_funded_feeds(
        self, now_timestamp: int, month_old_timestamp: int
    ) -> Tuple[Optional[List[QueryIdandFeedDetails]], ResponseStatus]:

        telliot_supported_feeds, status = await self.get_funded_feed_queries()

        if not status.ok:
            return None, status

        # remove feeds with price threshold > 0 and no api support
        catalog_supported_feeds = self.feed_filter.price_threshold_check_filter(telliot_supported_feeds)

        # make the first multicall and get current value, current index, and month old value index
        feeds_with_timestamp_index, status = await self.multi_call.timestamp_index_and_current_values_call(
            feeds=catalog_supported_feeds, month_old_timestamp=month_old_timestamp, now_timestamp=now_timestamp
        )

        if not status.ok:
            return None, status

        # filter out feeds where price threshold is zero but now timestamp not in window
        remove_uneligible_feeds = await self.feed_filter.filter_uneligible_feeds(
            feeds_with_timestamp_index, now_timestamp
        )

        if not remove_uneligible_feeds:
            msg = "All feeds were filtered out no feeds with eligible tips to report on"
            return None, ResponseStatus(error=msg)

        # multicall to get all timestamps for a query id in the past month
        feeds_with_timestamps_lis, status = await self.multi_call.timestamps_list_call(feeds=remove_uneligible_feeds)

        # return list of feeds if all query ids never had an oracle report
        if "No getTimestampbyQueryIdandIndex Calls to assemble" in status.error:
            return feeds_with_timestamp_index, ResponseStatus()

        # for each queryids timestamps list remove timestamp that wasn't eligible for tip
        timestamps_list_filtered = self.feed_filter.timestamps_filter(feeds_with_timestamps_lis)

        # get claim status count for every query ids eligible timestamp
        reward_claimed_status, status = await self.multi_call.rewards_claimed_status_call(timestamps_list_filtered)

        if reward_claimed_status is None:
            return timestamps_list_filtered, ResponseStatus()

        funded_feeds = self.feed_filter.get_real_balance(timestamps_list_filtered, reward_claimed_status)

        return funded_feeds, ResponseStatus()

    async def querydata_and_tip(self, current_time: TimeStamp) -> Optional[Dict[bytes, int]]:
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
