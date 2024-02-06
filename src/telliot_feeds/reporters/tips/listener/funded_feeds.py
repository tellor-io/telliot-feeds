"""Fetch and filter(based on telliot registry) funded queries from autopay
Make calls forward and fill in FullFeedQueryDetails
"""
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
from telliot_feeds.utils.query_search_utils import feed_in_feed_builder_mapping


logger = get_logger(__name__)


class FundedFeeds(FundedFeedFilter):
    """Fetch Feeds from autopay and filter"""

    def __init__(self, autopay: TellorFlexAutopayContract, multi_call: MulticallAutopay) -> None:
        self.multi_call = multi_call
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

        # List of feeds with telliot supported query types
        # TODO: make skipping manual feeds optional
        supported_funded_feeds = [
            (feed, query_data) for (feed, query_data) in funded_feeds if feed_in_feed_builder_mapping(query_data)
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

        qtype_supported_feeds, status = await self.get_funded_feed_queries()
        if not status.ok or not qtype_supported_feeds:
            return None, status

        # assemble both feed id and query id
        qtype_supported_feeds = self.generate_ids(feeds=qtype_supported_feeds)

        # make the first multicall and values and timestamps for the past month
        feeds_timestsamps_and_values_lis, status = await self.multi_call.month_of_timestamps_and_values(
            feeds=qtype_supported_feeds, now_timestamp=now_timestamp, max_age=month_old_timestamp, max_count=40_000
        )

        if not status.ok or not feeds_timestsamps_and_values_lis:
            return None, status

        # filter out feeds that aren't eligible to submit for NOW
        feeds_timestsamps_and_values_filtered = await self.window_and_priceThreshold_unmet_filter(
            feeds=feeds_timestsamps_and_values_lis, now_timestamp=now_timestamp
        )
        # for list of previous values, filter out any that weren't eligible for a tip
        historical_timestamps_list_filtered = self.filter_historical_submissions(
            feeds=feeds_timestsamps_and_values_filtered
        )

        # get claim status count for every query ids eligible timestamp
        reward_claimed_status, status = await self.multi_call.rewards_claimed_status_call(
            feeds=historical_timestamps_list_filtered
        )

        if reward_claimed_status is None:
            return historical_timestamps_list_filtered, ResponseStatus()

        funded_feeds = self.calculate_true_feed_balance(
            feeds=historical_timestamps_list_filtered, unclaimed_timestamps_count=reward_claimed_status
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
        # week_ago = current_time - 604_800
        # one_day_ago = current_time - 259_200

        eligible_funded_feeds, status = await self.filtered_funded_feeds(
            now_timestamp=current_time, month_old_timestamp=one_month_ago
        )
        if not status.ok:
            logger.error(f"Error getting eligible funded feeds: {status.error}")
            return None
        if not eligible_funded_feeds:
            logger.info("No eligible funded feeds found")
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
