"""To fetch tip amount for query_id when query tag selected in cli"""
from typing import List
from typing import Tuple
from typing import Optional

from telliot_feeds.reporters.tips.listener.dtypes import FeedDetails
from telliot_feeds.reporters.tips.listener.dtypes import QueryIdandFeedDetails
from telliot_feeds.reporters.tips.listener.utils import filter_batch_result
from telliot_feeds.reporters.tips.selected_queryid.selected_queryid_functions import CallFunctionSingle

from telliot_core.utils.response import ResponseStatus


class AutopayMulticall(CallFunctionSingle):
    """Make multicall batch call to get all relevant data to calculate feed tip eligibilty"""

    async def currentfeeds_databefore_timestampindexnow_timestampindexold(
        self, query_id: bytes, month_old_timestamp: int, now_timestamp: int
    ) -> Tuple[Optional[List[QueryIdandFeedDetails]], ResponseStatus]:
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

        # success equal to False handles any contract logic errors and return empty {}
        resp, status = await self.multi_call(calls, success=False)

        if not status.ok:
            return None, status

        if not resp:
            msg = "Empty response from multicall getCurrentFeeds..."
            status.ok = False
            status.error = msg
            return None, status

        # create QueryIdFeedDetails type that holds attributes of all response data
        feeds = []
        for feed_id in resp[query_id]:
            feed = QueryIdandFeedDetails(
                query_id=query_id,
                feed_id=feed_id,
                current_queryid_value=resp[("current_value", query_id)],
                current_value_timestamp=resp[("current_value_timestamp", query_id)],
                current_value_index=resp[("current_value_index", query_id)],
                month_old_index=resp[("month_old_index", query_id)]
            )
            feeds.append(feed)

        return feeds, status

    async def timestamp_datafeed(
        self, feeds: List[QueryIdandFeedDetails]
    ) -> Tuple[Optional[List[QueryIdandFeedDetails]], ResponseStatus]:
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
            status.ok = False
            status.error = msg
            return None, status

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
