"""Fetch and filter(based on telliot registry) funded queries from autopay
Make calls forward and fill in FullFeedQueryDetails
"""
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

from telliot_core.tellor.tellorflex.autopay import TellorFlexAutopayContract
from telliot_core.utils.timestamp import TimeStamp

from telliot_feeds.reporters.tip_listener.autopay_multicalls import AutopayMulticalls
from telliot_feeds.reporters.tip_listener.funded_feeds_filter import FundedFeedFilter
from telliot_feeds.reporters.tip_listener.utils_tip_listener import FeedDetails
from telliot_feeds.reporters.tip_listener.utils_tip_listener import FullFeedQueryDetails
from telliot_feeds.utils.log import get_logger


logger = get_logger(__name__)


class FundedFeeds:
    """Fetch Feeds from autopay and filter"""

    def __init__(
        self, autopay: TellorFlexAutopayContract, multi_call: AutopayMulticalls, feed_filter: FundedFeedFilter
    ) -> None:
        self.multi_call = multi_call
        self.feed_filter = feed_filter
        self.autopay = self.multi_call.autopay = autopay

    async def get_funded_feed_queries(self) -> Optional[List[FullFeedQueryDetails]]:
        """Call getFundedFeedDetails autopay function filter response data

        Return: list of tuples of only feed_details and query data
        that exist in telliot registry
        """
        funded_feeds: List[Tuple[FeedDetails, bytes]]
        funded_feeds, status = await self.autopay.read("getFundedFeedDetails")
        # funded_feeds, status = await self.feed_filter.autopay_function_call("getFundedFeedDetails")

        if not status.ok or not funded_feeds:
            logger.info("No funded feeds returned by autopay function call")
            return None

        for (details, query_data) in list(funded_feeds):
            # get data type name
            qtype_name = self.feed_filter.decode_typ_name(qdata=query_data)
            # bool response if query type supported by telliot
            if not self.feed_filter.qtype_name_in_registry(qtyp_name=qtype_name):
                funded_feeds.remove((details, query_data))

        if not funded_feeds:
            logger.info("No funded feeds with telliot support found in autopay")
            return None
        # create list of FullFeedQueryDetails data type to hold all relevant info about a feed
        # including its corresponding query ids timestamps and current values
        funded_feed_details = [FullFeedQueryDetails(*funded_feed) for funded_feed in funded_feeds]

        return funded_feed_details

    async def filter_funded_feeds(
        self, now_timestamp: int, monthold_timestamp: int
    ) -> Optional[List[FullFeedQueryDetails]]:
        telliot_supported_feeds = await self.get_funded_feed_queries()
        if not telliot_supported_feeds:
            logger.info("No funded feeds available in autopay!")
            return None
        # remove feeds with price threshold > 0 and no api support to check threshold
        catalog_supported_feeds = self.feed_filter.price_threshold_check_filter(telliot_supported_feeds)

        # check timestamps for window eligibilty before reward call
        # start autopay calls with multicall
        # sigs: getDataBefore, getIndexforDataBefore x2
        feeds_with_timestamp_index = await self.multi_call.timestamp_index_and_current_values_call(
            feeds=catalog_supported_feeds, month_old_timestamp=monthold_timestamp, now_timestamp=now_timestamp
        )

        # after getting current values to check against, if price threshold == 0
        # check if timestamp now first in window
        for feed_detail in list(feeds_with_timestamp_index):
            if feed_detail.feed_details.priceThreshold == 0:
                # check if your timestamp will be first in window for
                # this feed if not discard feed_details
                # lesser node calls to make
                in_eligible_window, time_based_reward = self.feed_filter.is_timestamp_first_in_window(
                    feed_interval=feed_detail.feed_details.interval,
                    feed_start_timestamp=feed_detail.feed_details.startTime,
                    feed_window=feed_detail.feed_details.window,
                    timestamp_before=feed_detail.current_value_timestamp,
                    timestamp_to_check=now_timestamp,
                )
                feed_detail.feed_details.reward += feed_detail.feed_details.rewardIncreasePerSecond * time_based_reward
                if not in_eligible_window:
                    # if now_timestamp is not in eligible window, discard funded feed
                    # remove feedId from feedId to queryId mapping
                    # discard funded feed
                    feeds_with_timestamp_index.remove(feed_detail)

        if not feeds_with_timestamp_index:
            print("All feeds were filtered out no feeds with eligible tips to report on")
            return None

        feeds_with_timestamps_lis = await self.multi_call.timestamps_list_call(feeds=feeds_with_timestamp_index)

        if not feeds_with_timestamps_lis:
            logger.info("No submission reports for all query ids")
            return feeds_with_timestamp_index
        # after getting a timestamp list for all reported values for every query id
        # filter out timestamps that aren't first in a feeds eligible window
        for feed_detail in feeds_with_timestamps_lis:
            # if feed_detail.feed_details.priceThreshold != 0 or len(feed_detail.queryId_timestamps_list) < 2:
            #     continue
            if len(feed_detail.queryId_timestamps_list) < 2:
                continue
            for i, _ in enumerate(list(feed_detail.queryId_timestamps_list)):
                in_eligibile_window = self.feed_filter.is_timestamp_first_in_window(
                    timestamp_before=feed_detail.queryId_timestamps_list[i - 2],
                    timestamp_to_check=feed_detail.queryId_timestamps_list[i - 1],
                    feed_start_timestamp=feed_detail.feed_details.startTime,
                    feed_window=feed_detail.feed_details.window,
                    feed_interval=feed_detail.feed_details.interval,
                )
                if not in_eligibile_window:
                    feed_detail.queryId_timestamps_list.remove(feed_detail.details.timestamps[i - 1])
        # get claim status count for every query ids eligible timestamp per feed
        reward_claimed_status = await self.multi_call.rewards_claimed_status_call(feeds_with_timestamps_lis)

        if reward_claimed_status is None:
            return feeds_with_timestamps_lis
        # reduce balance based on unclaimed count of reported timestamps
        for feed_detail in list(feeds_with_timestamps_lis):
            key = (feed_detail.feed_id, feed_detail.query_id)
            unclaimed_count = reward_claimed_status[key]
            feed_detail.feed_details.balance -= feed_detail.feed_details.reward * unclaimed_count
            # if remaining balance is zero filter out the feed from the dictionary
            if feed_detail.feed_details.balance <= 0:
                feeds_with_timestamps_lis.remove(feed_detail)

        return feeds_with_timestamps_lis

    async def get_feed_tips(self) -> Optional[Dict[bytes, int]]:
        current_time = TimeStamp.now().ts
        one_month_ago = current_time - 2_592_000

        eligible_funded_feeds: Optional[List[FullFeedQueryDetails]] = await self.filter_funded_feeds(
            now_timestamp=current_time, monthold_timestamp=one_month_ago
        )
        if not eligible_funded_feeds:
            return None
        # dictionary of key: queryData with value: tipAmount
        query_data_with_tip = {}
        for funded_feed in list(eligible_funded_feeds):
            query_data = funded_feed.query_data
            if funded_feed.feed_details.priceThreshold != 0:
                window_eligiblity, time_based_reward = self.feed_filter.is_timestamp_first_in_window(
                    timestamp_before=funded_feed.current_value_timestamp,
                    timestamp_to_check=current_time,
                    feed_start_timestamp=funded_feed.feed_details.startTime,
                    feed_window=funded_feed.feed_details.window,
                    feed_interval=funded_feed.feed_details.interval,
                )
                funded_feed.feed_details.reward += funded_feed.feed_details.rewardIncreasePerSecond * time_based_reward
                if window_eligiblity is False:
                    price_change = await self.feed_filter.price_change(
                        query_id=funded_feed.query_id,  # type: ignore
                        value_before=int(int(funded_feed.current_value.hex(), 16) / 10**18),
                    )
                    if price_change is None:
                        continue
                    if price_change > funded_feed.feed_details.priceThreshold:
                        if query_data not in query_data_with_tip:
                            query_data_with_tip[query_data] = funded_feed.feed_details.reward
                        else:
                            query_data_with_tip[query_data] += funded_feed.feed_details.reward

            elif funded_feed.feed_details.priceThreshold == 0:
                if query_data not in query_data_with_tip:
                    query_data_with_tip[query_data] = funded_feed.feed_details.reward
                else:
                    query_data_with_tip[query_data] += funded_feed.feed_details.reward

        return query_data_with_tip
