from typing import Optional

from eth_utils.conversions import to_bytes
from telliot_core.utils.response import error_status
from telliot_core.utils.response import ResponseStatus

from telliot_feeds.reporters.tips.funded_feeds.call_functions import CallFunctions
from telliot_feeds.reporters.tips.listener.dtypes import QueryIdandFeedDetails
from telliot_feeds.reporters.tips.listener.utils import filter_batch_result
from telliot_feeds.reporters.tips.listener.utils import handler_func
from telliot_feeds.reporters.tips.listener.dtypes import FeedDetails


class MulticallAutopay(CallFunctions):
    # make the calls
    async def timestamp_index_and_current_values_call(
        self, feeds: list[QueryIdandFeedDetails], month_old_timestamp: int, now_timestamp: int
    ) -> tuple[Optional[list[QueryIdandFeedDetails]], ResponseStatus]:
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
            return None, error_status("Unable to assemble getDataBefore Call object")

        databefore_resp, status = await self.multi_call(calls)

        if not status.ok:
            return None, status

        if not databefore_resp:
            return None, error_status("No response returned from getDataBefore batch multicall")

        for feed in feeds:
            # set QueryIdandFeedDetails attributes
            feed.current_value_timestamp = databefore_resp[("current_value_timestamp", feed.query_id)]
            feed.current_queryid_value = databefore_resp[("current_value", feed.query_id)]
            feed.current_value_index = databefore_resp[("current_value_index", feed.query_id)]
            feed.month_old_index = databefore_resp[("month_old_index", feed.query_id)]

        return feeds, status

    async def timestamps_list_call(
        self, feeds: list[QueryIdandFeedDetails]
    ) -> tuple[Optional[list[QueryIdandFeedDetails]], ResponseStatus]:
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
            return None, error_status("No getTimestampbyQueryIdandIndex Calls to assemble")

        timestampby_queryid_index_resp, status = await self.multi_call(calls)

        if not status.ok:
            return None, status

        if not timestampby_queryid_index_resp:
            return None, error_status("No response returned from getTimestampbyQueryIdandIndex batch multicall")

        # converts from: {(current_value, queryid): 0, (current_timestamp, queryid): 123}
        # to: {queryid: [0, 123]}
        clean_resp = filter_batch_result(timestampby_queryid_index_resp)

        for feed in feeds:
            feed.queryId_timestamps_list = clean_resp[feed.query_id]

        return feeds, status

    async def rewards_claimed_status_call(
        self, feeds: list[QueryIdandFeedDetails]
    ) -> tuple[Optional[dict[tuple[Optional[bytes], Optional[bytes]], int]], ResponseStatus]:
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
            return None, error_status("No getRewardClaimStatusList Calls to assemble")

        reward_claimed_status_resp, status = await self.multi_call(calls, success=True)

        if not status.ok:
            return None, status

        if not reward_claimed_status_resp:
            return None, error_status("No response returned from getRewardClaimStatusList batch multicall")

        return reward_claimed_status_resp, status

    async def currentfeeds_databefore_timestampindexnow_timestampindexold(
        self, query_id: bytes, month_old_timestamp: int, now_timestamp: int
    ) -> tuple[Optional[list[QueryIdandFeedDetails]], ResponseStatus]:
        """Batch call two functions (getDataBefore,getIndexForDataBefore)

        Args:
        - now_timestamp: current time in unix timestamps
        - month_old_timestamp: now_timestamp - 2_592_000

        Return: a list of QueryIdandFeedDetails

        fetches:
        - list of feed_ids
        - most recent value and timestamp and index
        - month old value index
        >>> example response from multicall looks like
        {
            b'query_id': [b'feed_id',],
            ("current_value_timestamp", b'query_id'): 123, ("current_value", b'query_id'): b'',
            ("current_status", b'query_id'): True, ("current_value_index", b'query_id'): 1,
            ("month_old_status", b'query_id'): True, ("month_old_index", b'query_id'): 1
        }
        """
        calls = [
            self.get_current_feeds(query_id=query_id),
            self.get_data_before(query_id=query_id, now_timestamp=now_timestamp),
            self.get_index_for_data_before_now(query_id=query_id, now_timestamp=now_timestamp),
            self.get_index_for_data_before_month(query_id=query_id, month_old=month_old_timestamp),
        ]

        resp, status = await self.multi_call(calls)

        if not status.ok:
            return None, status

        if not resp:
            msg = "Empty response from multicall getCurrentFeeds..."
            return None, error_status(msg)

        # create QueryIdFeedDetails type that holds attributes of all response data
        feeds = []
        for feed_id in resp[query_id]:
            feed = QueryIdandFeedDetails(
                query_id=query_id,
                feed_id=feed_id,
                current_queryid_value=resp[("current_value", query_id)],
                current_value_timestamp=resp[("current_value_timestamp", query_id)],
                current_value_index=resp[("current_value_index", query_id)],
                month_old_index=resp[("month_old_index", query_id)],
            )
            feeds.append(feed)

        return feeds, status

    async def timestamp_datafeed(
        self, feeds: list[QueryIdandFeedDetails]
    ) -> tuple[Optional[list[QueryIdandFeedDetails]], ResponseStatus]:
        """Batch call getTimestampbyQueryIdandIndex to fetch a list of timestamps for each query id

        Args:
        - feeds: a list of QueryIdandFeedDetails object

        Return: a list of QueryIdandFeedDetails object
        """
        calls = []
        for feed in feeds:
            calls.append(self.get_data_feed(feed.feed_id))
            if feed.current_value_index > 0:
                for i in range(feed.month_old_index, feed.current_value_index + 1):
                    calls.append(self.get_timestamp_by_query_id_and_index(feed.query_id, index=i))

        resp, status = await self.multi_call(calls)

        if not status.ok:
            return None, status

        if not resp:
            msg = "Couldn't fetch feed details for current feeds"
            return None, error_status(msg)

        # separate dictionary response
        for feed in feeds:
            # set feed_details attribute and delete from response dictionary
            feed.params = FeedDetails(*resp[feed.feed_id])
            del resp[feed.feed_id]

        # refactor response dictionary for easy access setting the queryid_timestamps attribute
        clean_resp = filter_batch_result(resp)

        for feed in feeds:
            # set queryid_timestamps attr with list of timestamps of queryids months long report submission
            feed.queryid_timestamps = clean_resp[feed.query_id]

        return feeds, status
