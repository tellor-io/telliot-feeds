import math

from typing import Tuple
from typing import List
from typing import Optional
from eth_utils.conversions import to_bytes
from eth_abi import encode_single
from web3 import Web3 as w3

from telliot_feeds.reporters.tip_listener.tip_listener_filter import TipListenerFilter
from telliot_feeds.reporters.tip_listener.utils_tip_listener import FullFeedQueryDetails
from telliot_feeds.feeds import CATALOG_FEEDS
from telliot_feeds.queries.query_catalog import query_catalog
from telliot_core.utils.response import error_status
from telliot_feeds.utils.log import get_logger

logger = get_logger(__name__)
# Mapping of queryId to query tag for supported queries
CATALOG_QUERY_IDS = {query_catalog._entries[tag].query.query_id: tag for tag in query_catalog._entries}


class FundedFeedFilter(TipListenerFilter):
    def generate_ids(self, feed: FullFeedQueryDetails) -> Tuple[bytes, bytes]:
        """Hash feed details to generate query id and feed id

        Return:
        - query_id: keccak(query_data)
        - feed_id: keccak(abi.encode(queryId,reward,startTime,interval,window,priceThreshold,rewardIncreasePerSecond)
        """

        feed_details = feed.feed_details
        query_id = to_bytes(hexstr=w3.keccak(feed.query_data).hex())
        feed_data = encode_single(
            "(bytes32,uint256,uint256,uint256,uint256,uint256,uint256)",
            [
                query_id,
                feed_details.reward,
                feed_details.startTime,
                feed_details.interval,
                feed_details.window,
                feed_details.priceThreshold,
                feed_details.rewardIncreasePerSecond,
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
        datafeed = CATALOG_FEEDS[query_tag]
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

    def price_threshold_check_filter(self, feeds: List[FullFeedQueryDetails]) -> List[FullFeedQueryDetails]:
        """Filter funded feeds based on threshold and telliot catalog feeds
        """
        for feed in list(feeds):
            feed_id, query_id = self.generate_ids(feed)
            feed.feed_id = feed_id
            feed.query_id = query_id
            if feed.feed_details.priceThreshold > 0 and CATALOG_QUERY_IDS[query_id] not in CATALOG_FEEDS:
                feeds.remove(feed)
        return feeds
