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
    ) -> Optional[List[QueryIdandFeedDetails]]:

        telliot_supported_feeds, status = await self.get_funded_feed_queries()

        if not status.ok:
            logger.info(status.error)
            return None

        # remove feeds with price threshold > 0 and no api support to check threshold
        catalog_supported_feeds = self.feed_filter.price_threshold_check_filter(telliot_supported_feeds)

        # check timestamps for window eligibilty before reward call
        # start autopay calls with multicall
        # sigs: getDataBefore, getIndexforDataBefore x2
        feeds_with_timestamp_index, status = await self.multi_call.timestamp_index_and_current_values_call(
            feeds=catalog_supported_feeds, month_old_timestamp=month_old_timestamp, now_timestamp=now_timestamp
        )

        if not status.ok:
            logger.info(status.error)
            return None
        # after getting current values to check against, if price threshold == 0
        # check if timestamp now first in window
        remove_uneligible_feeds = await self.feed_filter.filter_uneligible_feeds(
            feeds_with_timestamp_index, now_timestamp
        )

        if not remove_uneligible_feeds:
            logger.info("All feeds were filtered out no feeds with eligible tips to report on")
            return None

        feeds_with_timestamps_lis, status = await self.multi_call.timestamps_list_call(feeds=remove_uneligible_feeds)

        if "No getTimestampbyQueryIdandIndex Calls to assemble" in status.error:
            return feeds_with_timestamp_index

        # after getting a timestamp list for all reported values for every query id
        # filter out timestamps that aren't first in a feeds eligible window
        timestamps_list_filtered = self.feed_filter.timestamps_filter(feeds_with_timestamps_lis)

        # get claim status count for every query ids eligible timestamp per feed
        reward_claimed_status, status = await self.multi_call.rewards_claimed_status_call(timestamps_list_filtered)

        if reward_claimed_status is None:
            return feeds_with_timestamps_lis

        funded_feeds = self.feed_filter.get_real_balance(feeds_with_timestamps_lis, reward_claimed_status)

        return funded_feeds

    async def querydata_and_tip(self) -> Optional[Dict[bytes, int]]:
        current_time = TimeStamp.now().ts
        one_month_ago = current_time - 2_592_000

        eligible_funded_feeds: Optional[List[QueryIdandFeedDetails]] = await self.filtered_funded_feeds(
            now_timestamp=current_time, month_old_timestamp=one_month_ago
        )
        if not eligible_funded_feeds:
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
