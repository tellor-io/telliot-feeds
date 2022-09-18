"""Batch call autopay functions"""
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

from eth_utils.conversions import to_bytes
from telliot_core.utils.response import ResponseStatus

from telliot_feeds.reporters.tips.funded_feeds.call_functions import CallFunctions
from telliot_feeds.reporters.tips.listener.dtypes import QueryIdandFeedDetails
from telliot_feeds.reporters.tips.listener.utils import filter_batch_result
from telliot_feeds.reporters.tips.listener.utils import handler_func


class MulticallAutopay(CallFunctions):
    # make the calls
    async def timestamp_index_and_current_values_call(
        self, feeds: List[QueryIdandFeedDetails], month_old_timestamp: int, now_timestamp: int
    ) -> Tuple[Optional[List[QueryIdandFeedDetails]], ResponseStatus]:
        """Batch call two functions (getDataBefore,getIndexForDataBefore)

        Args:
        - now_timestamp: current time in unix timestamps
        - month_old_timestamp: now_timestamp - 2_592_000

        Return: a list of QueryIdandFeedDetails
        to be used in the next batch call that fetches a list of timestamps for each queryId
        """
        calls = []
        for feed in feeds:
            calls += [
                self.get_data_before(query_id=feed.query_id, now_timestamp=now_timestamp),
                self.get_index_for_data_before_now(query_id=feed.query_id, now_timestamp=now_timestamp),
                self.get_index_for_data_before_month(query_id=feed.query_id, month_old=month_old_timestamp),
            ]

        if not len(calls):
            return None, ResponseStatus(ok=False, error="Unable to assemble getDataBefore Call object")

        # success equal to False handles any contract logic errors and return empty {}
        databefore_resp, status = await self.multi_call(calls, success=False)

        if not status.ok:
            return None, status

        if not databefore_resp:
            return None, ResponseStatus(ok=False, error="No response returned from getDataBefore batch multicall")

        # filter data out here
        for feed in feeds:
            # set QueryIdandFeedDetails attributes
            feed.current_value_timestamp = databefore_resp[("current_value_timestamp", feed.query_id)]
            feed.current_queryid_value = databefore_resp[("current_value", feed.query_id)]
            feed.current_value_index = databefore_resp[("current_value_index", feed.query_id)]
            feed.month_old_index = databefore_resp[("month_old_index", feed.query_id)]

        return feeds, status

    async def timestamps_list_call(
        self, feeds: List[QueryIdandFeedDetails]
    ) -> Tuple[Optional[List[QueryIdandFeedDetails]], ResponseStatus]:
        """Batch call getTimestampbyQueryIdandIndex to fetch a list of timestamps for each query id

        Args:
        - feeds: a list of QueryIdandFeedDetails object

        Return: a list of QueryIdandFeedDetails object that carries query id and its month long timestamps list
        """
        calls = [
            self.get_timestamp_by_query_id_and_index(to_bytes(hexstr=feed.query_id), index=idx)
            for feed in feeds
            for idx in range(feed.month_old_index, feed.current_value_index)
        ]

        if not len(calls):
            return None, ResponseStatus(ok=False, error="No getTimestampbyQueryIdandIndex Calls to assemble")

        timestampby_queryid_index_resp, status = await self.multi_call(calls)

        if not status.ok:
            return None, status

        if not timestampby_queryid_index_resp:
            return None, ResponseStatus(
                ok=False, error="No response returned from getTimestampbyQueryIdandIndex batch multicall"
            )

        clean_resp = filter_batch_result(timestampby_queryid_index_resp)

        for feed in feeds:
            feed.queryId_timestamps_list = clean_resp[feed.query_id]

        return feeds, status

    async def rewards_claimed_status_call(
        self, feeds: List[QueryIdandFeedDetails]
    ) -> Tuple[Optional[Dict[Tuple[Optional[bytes], Optional[bytes]], int]], ResponseStatus]:
        """Batch call getRewardClaimStatusList

        Args:
        - feeds: list QueryIdandFeedDetails

        Return: dict with count of unclaimed timestamps
        """
        calls = [
            self.get_reward_claimed_status(feed.feed_id, feed.query_id, feed.queryid_timestamps_list, handler_func)
            for feed in feeds
            if feed.queryid_timestamps_list
        ]

        if not len(calls):
            return None, ResponseStatus(ok=False, error="No getRewardClaimStatusList Calls to assemble")

        reward_claimed_status_resp, status = await self.multi_call(calls, success=True)

        if not status.ok:
            return None, status

        if not reward_claimed_status_resp:
            return None, ResponseStatus(
                ok=False, error="No response returned from getRewardClaimStatusList batch multicall"
            )

        return reward_claimed_status_resp, status
