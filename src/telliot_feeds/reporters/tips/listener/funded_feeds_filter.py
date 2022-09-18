import math
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

from eth_abi import encode_single
from eth_utils.conversions import to_bytes
from telliot_core.utils.response import error_status
from telliot_core.utils.timestamp import TimeStamp
from web3 import Web3 as w3

from telliot_feeds.feeds import CATALOG_FEEDS
from telliot_feeds.feeds import LEGACY_DATAFEEDS
from telliot_feeds.reporters.tips import CATALOG_QUERY_IDS
from telliot_feeds.reporters.tips.listener.dtypes import QueryIdandFeedDetails
from telliot_feeds.reporters.tips.listener.tip_listener_filter import TipListenerFilter
from telliot_feeds.utils.log import get_logger

logger = get_logger(__name__)


class FundedFeedFilter(TipListenerFilter):
    def generate_ids(self, feed: QueryIdandFeedDetails) -> Tuple[bytes, bytes]:
        """Hash feed details to generate query id and feed id

        Return:
        - query_id: keccak(query_data)
        - feed_id: keccak(abi.encode(queryId,reward,startTime,interval,window,priceThreshold,rewardIncreasePerSecond)
        """
        query_id = to_bytes(hexstr=w3.keccak(feed.query_data).hex())
        feed_data = encode_single(
            "(bytes32,uint256,uint256,uint256,uint256,uint256,uint256)",
            [
                query_id,
                feed.params.reward,
                feed.params.startTime,
                feed.params.interval,
                feed.params.window,
                feed.params.priceThreshold,
                feed.params.rewardIncreasePerSecond,
            ],
        )
        feed_id = to_bytes(hexstr=w3.keccak(feed_data).hex())
        return feed_id, query_id

    def is_timestamp_first_in_window(
        self,
        timestamp_before: int,
        timestamp_to_check: int,
        feed_start_timestamp: int,
        feed_window: int,
        feed_interval: int,
    ) -> Tuple[bool, int]:
        """
        Calculates to check if timestamp(timestamp_to_check) is first in window

        Return: bool
        """
        # if all(i is None for i in [
        #     timestamp_before, timestamp_to_check, feed_start_timestamp, feed_window, feed_interval
        # ]):
        #     return False, None
        # Number of intervals since start time
        num_intervals = math.floor((timestamp_to_check - feed_start_timestamp) / feed_interval)
        # Start time of latest submission window
        current_window_start = feed_start_timestamp + (feed_interval * num_intervals)
        time_diff = timestamp_to_check - current_window_start
        eligible = [time_diff < feed_window, timestamp_before < current_window_start]
        return all(eligible), time_diff

    async def price_change(self, query_id: bytes, value_before: int) -> Optional[float]:
        # check price threshold is met
        query_tag = CATALOG_QUERY_IDS[query_id]

        if query_tag in CATALOG_FEEDS:
            datafeed = CATALOG_FEEDS[query_tag]
        elif query_tag in LEGACY_DATAFEEDS:
            datafeed = LEGACY_DATAFEEDS[query_tag]
        else:
            print("Can't fetch price for priceThreshold check")
            return None

        value_now = await datafeed.source.fetch_new_datapoint()  # type: ignore

        if not value_now:
            note = f"Unable to fetch {datafeed} price for tip calculation"
            error_status(note=note, log=logger.warning)
            return None

        value_now = value_now[0]

        if value_before == 0:
            price_change = 10000

        elif value_now >= value_before:
            price_change = (10000 * (value_now - value_before)) / value_before

        else:
            price_change = (10000 * (value_before - value_now)) / value_before

        return price_change

    def price_threshold_check_filter(self, feeds: List[QueryIdandFeedDetails]) -> List[QueryIdandFeedDetails]:
        """Filter funded feeds based on threshold and telliot catalog feeds"""
        for feed in list(feeds):
            feed_id, query_id = self.generate_ids(feed)
            feed.feed_id = feed_id
            feed.query_id = query_id
            tag = CATALOG_QUERY_IDS[query_id]
            if feed.params.priceThreshold > 0 and (tag not in CATALOG_FEEDS or tag not in LEGACY_DATAFEEDS):
                feeds.remove(feed)
        return feeds

    def timestamps_filter(self, feeds: List[QueryIdandFeedDetails]) -> List[QueryIdandFeedDetails]:
        for feed in feeds:
            if len(feed.queryid_timestamps_list) < 2:
                continue
            for i, _ in enumerate(list(feed.queryid_timestamps_list)):
                in_eligibile_window = self.is_timestamp_first_in_window(
                    timestamp_before=feed.queryid_timestamps_list[i - 2],
                    timestamp_to_check=feed.queryid_timestamps_list[i - 1],
                    feed_start_timestamp=feed.params.startTime,
                    feed_window=feed.params.window,
                    feed_interval=feed.params.interval,
                )
                if not in_eligibile_window:
                    # check price change
                    feed.queryid_timestamps_list.remove(feed.queryid_timestamps_list[i - 1])
        return feeds

    def get_real_balance(
        self, feeds: List[QueryIdandFeedDetails], unclaimed_timestamps_count: Dict[Tuple[bytes, bytes], int]
    ) -> List[QueryIdandFeedDetails]:
        # reduce balance based on unclaimed count of reported timestamps
        for feed in list(feeds):
            key = (feed.feed_id, feed.query_id)
            unclaimed_count = unclaimed_timestamps_count[key]
            feed.params.balance -= feed.params.reward * unclaimed_count
            # if remaining balance is zero filter out the feed from the dictionary
            if feed.params.balance <= 0:
                feeds.remove(feed)
        return feeds

    async def filter_uneligible_feeds(
        self, feeds: List[QueryIdandFeedDetails], now_timestamp: TimeStamp
    ) -> List[QueryIdandFeedDetails]:
        for feed in list(feeds):
            # check if your timestamp will be first in window for
            # this feed if not discard feed_details
            # lesser node calls to make
            in_eligible_window, time_diff = self.is_timestamp_first_in_window(
                feed_interval=feed.params.interval,
                feed_start_timestamp=feed.params.startTime,
                feed_window=feed.params.window,
                timestamp_before=feed.current_value_timestamp,
                timestamp_to_check=now_timestamp,
            )

            balance = feed.params.balance
            price_threshold = feed.params.priceThreshold

            if in_eligible_window:
                sloped_reward = feed.params.rewardIncreasePerSecond * time_diff
                feed.params.reward += sloped_reward
                if balance < feed.params.reward:
                    feeds.remove(feed)
                continue

            if price_threshold != 0:
                try:
                    value_before = int(int(feed.current_queryid_value.hex(), 16) / 10**18)
                except ValueError:
                    error_status("Error decoding current query id value")
                    continue
                price_change = await self.price_change(
                    query_id=feed.query_id,
                    value_before=value_before,
                )
                if price_change is None:
                    # unable to fetch price data
                    continue
                if price_change < price_threshold and not in_eligible_window:
                    feeds.remove(feed)
                    continue

            if price_threshold == 0:
                if not in_eligible_window:
                    # if now_timestamp is not in eligible window, discard funded feed
                    # remove feedId from feedId to queryId mapping
                    # discard funded feed
                    feeds.remove(feed)
                    continue
        return feeds
