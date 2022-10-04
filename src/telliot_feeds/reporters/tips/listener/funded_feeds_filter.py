import math
from typing import Optional

from eth_abi import encode_single
from eth_utils.conversions import to_bytes
from telliot_core.utils.response import error_status
from telliot_core.utils.timestamp import TimeStamp
from web3 import Web3 as w3

from telliot_feeds.feeds import CATALOG_FEEDS
from telliot_feeds.reporters.tips import CATALOG_QUERY_IDS
from telliot_feeds.reporters.tips.listener.dtypes import QueryIdandFeedDetails
from telliot_feeds.utils.log import get_logger

logger = get_logger(__name__)


class FundedFeedFilter:
    def generate_ids(self, feed: QueryIdandFeedDetails) -> tuple[bytes, bytes]:
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
    ) -> tuple[bool, int]:
        """
        Checks if timestamp is first in window

        Args:
        - timestamp_before: the timestamp to check against
        - timetamp_to_check: the timestamp thats checked if its first in window
        - feed_start_timestamp
        - feed_window
        - feed_interval

        Return: bool
        """
        # Number of intervals since start time
        num_intervals = math.floor((timestamp_to_check - feed_start_timestamp) / feed_interval)
        # Start time of latest submission window
        current_window_start = feed_start_timestamp + (feed_interval * num_intervals)
        time_diff = timestamp_to_check - current_window_start
        eligible = [time_diff < feed_window, timestamp_before < current_window_start]
        return all(eligible), time_diff

    async def price_change(self, query_id: bytes, value_before: int) -> Optional[float]:
        """Check if priceThreshold is met

        Args:
        - query_id: used to get api source
        - value_before: the value used to compare current value

        Returns: float
        """
        if query_id not in CATALOG_QUERY_IDS:
            return None

        query_tag = CATALOG_QUERY_IDS[query_id]

        if query_tag in CATALOG_FEEDS:
            datafeed = CATALOG_FEEDS[query_tag]
        else:
            logger.info(f"No Api source found for {query_tag} to check priceThreshold")
            return None

        value_now = await datafeed.source.fetch_new_datapoint()  # type: ignore

        if not value_now:
            note = f"Unable to fetch {datafeed} price for tip calculation"
            _ = error_status(note=note, log=logger.warning)
            return None

        value_now = value_now[0]

        # catch price change up to 0.01 percent granularity
        # could be done differently but this way is consistent with autopay contract
        if value_before == 0:
            # if no before value set price change to 100 percent
            price_change = 10000

        elif value_now >= value_before:

            price_change = (10000 * (value_now - value_before)) / value_before

        else:
            price_change = (10000 * (value_before - value_now)) / value_before

        return price_change

    def api_support_check(self, feeds: list[QueryIdandFeedDetails]) -> list[QueryIdandFeedDetails]:
        """Filter funded feeds where threshold is gt zero and no telliot catalog feeds support"""
        telliot_supported_with_api = [
            feed
            for feed in feeds
            if feed.params.priceThreshold == 0
            or (feed.query_id in CATALOG_QUERY_IDS and CATALOG_QUERY_IDS[feed.query_id] in CATALOG_FEEDS)
        ]

        return telliot_supported_with_api

    def timestamps_filter(self, feeds: list[QueryIdandFeedDetails]) -> list[QueryIdandFeedDetails]:
        """list of timestamps compared against itself"""
        for feed in feeds:
            # in case a query id has has none or too few to compare
            if len(feed.queryid_timestamps_list) < 2:
                continue
            for i in range(len(feed.queryid_timestamps_list)):
                in_eligibile_window = self.is_timestamp_first_in_window(
                    timestamp_before=feed.queryid_timestamps_list[i - 2],
                    timestamp_to_check=feed.queryid_timestamps_list[i - 1],
                    feed_start_timestamp=feed.params.startTime,
                    feed_window=feed.params.window,
                    feed_interval=feed.params.interval,
                )
                if not in_eligibile_window:
                    feed.queryid_timestamps_list.remove(feed.queryid_timestamps_list[i - 1])
        return feeds

    def calculate_true_feed_balance(
        self, feeds: list[QueryIdandFeedDetails], unclaimed_timestamps_count: dict[tuple[bytes, bytes], int]
    ) -> list[QueryIdandFeedDetails]:
        """Reduce balance based on unclaimed count of reported timestamps

        Args:
        - feeds: list of feeds
        - unclaimed_timestamps_count: dict of queryid to unclaimed timestamps count

        Returns: list of feeds
        """
        for feed in list(feeds):
            key = (feed.feed_id, feed.query_id)
            unclaimed_count = unclaimed_timestamps_count[key]
            feed.params.balance -= feed.params.reward * unclaimed_count
            # if remaining balance is zero filter out the feed from the list
            if feed.params.balance <= 0:
                feeds.remove(feed)
        return feeds

    async def window_and_priceThreshold_unmet_filter(
        self, feeds: list[QueryIdandFeedDetails], now_timestamp: TimeStamp
    ) -> list[QueryIdandFeedDetails]:

        """Remove feeds from list that either submitting now won't be first in window
        or price threshold is not met

        Args:
        - feeds: list of feeds
        - now_timestamp: current timestamp used to check if first in window

        Returns: list of feeds that could possibly reward a tip
        """
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
            elif price_threshold == 0 and not in_eligible_window:
                # if now_timestamp is not in eligible window, discard funded feed
                # remove feedId from feedId to queryId mapping
                # discard funded feed
                feeds.remove(feed)
                continue

            if price_threshold != 0 and not in_eligible_window:
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
                if price_change < price_threshold:
                    feeds.remove(feed)
                    continue

        return feeds
