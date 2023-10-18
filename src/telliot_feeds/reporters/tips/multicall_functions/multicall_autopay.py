from typing import Any
from typing import Optional

from telliot_core.utils.response import error_status
from telliot_core.utils.response import ResponseStatus

from telliot_feeds.datafeed import DataFeed
from telliot_feeds.reporters.tips.listener.dtypes import FeedDetails
from telliot_feeds.reporters.tips.listener.dtypes import QueryIdandFeedDetails
from telliot_feeds.reporters.tips.listener.dtypes import Values
from telliot_feeds.reporters.tips.listener.utils import handler_func
from telliot_feeds.reporters.tips.multicall_functions.call_functions import CallFunctions


class MulticallAutopay(CallFunctions):
    # make the calls
    async def month_of_timestamps_and_values(
        self, feeds: list[QueryIdandFeedDetails], now_timestamp: int, max_age: int, max_count: int
    ) -> tuple[Optional[list[QueryIdandFeedDetails]], ResponseStatus]:
        """Getter for a month long of timestamps and values for every query id

        Args:
        - now_timestamp: current time in unix timestamps
        - month_old_timestamp: now_timestamp - 2_592_000

        Return: a list of QueryIdandFeedDetails
        to be used in the next batch call that fetches a list of timestamps for each queryId
        """

        unique_ids = {feed.query_id for feed in feeds}

        calls = [
            self.get_multiple_values_before(
                query_id=qid, now_timestamp=now_timestamp, max_age=max_age, max_count=max_count
            )
            for qid in unique_ids
        ]
        if not len(calls):
            return None, error_status("Unable to assemble getMultipleValues Call object")

        multiple_values_response, status = await self.multi_call(calls)

        if not status.ok:
            return None, status

        if not multiple_values_response:
            return None, error_status("No response returned from getMultipleValuesBefore batch multicall")

        for feed in feeds:
            values_tup = ("values_array", feed.query_id)
            timestamps_tup = ("timestamps_array", feed.query_id)
            if values_tup not in multiple_values_response:
                note = f"values_tup not in multiple_values_response: ('values_array', 0x{feed.query_id.hex()})"
                return None, error_status(note)
            if timestamps_tup not in multiple_values_response:
                note = f"timestamps_tup not in multiple_values_response: ('timestamps_array', 0x{feed.query_id.hex()})"
                return None, error_status(note)
            values = multiple_values_response[values_tup]
            timestamps = multiple_values_response[timestamps_tup]
            # remove old timestamps
            if timestamps:
                timestamps = [
                    timestamp for timestamp in timestamps if timestamp > max_age and timestamp >= feed.params.startTime
                ]
            # short circuit the loop since None means failed response and can't calculate tip accurately
            if values is None:
                note = "getMultipleValuesBefore call failed"
                return None, error_status(note)
            feed.current_value_timestamp = timestamps[-1] if timestamps else 0
            feed.current_queryid_value = values[-1] if values else b""

            feed.queryid_timestamps_values_list = list(map(Values, values, timestamps))

        return feeds, status

    async def rewards_claimed_status_call(
        self, feeds: list[QueryIdandFeedDetails]
    ) -> tuple[Optional[dict[tuple[bytes, bytes], int]], ResponseStatus]:
        """Batch call getRewardClaimStatusList

        Args:
        - feeds: list QueryIdandFeedDetails

        Return: dict with count of unclaimed timestamps
        """
        calls = []
        for feed in feeds:
            if feed.queryid_timestamps_values_list:
                timestamps_lis = [values.timestamp for values in feed.queryid_timestamps_values_list]
                calls.append(self.get_reward_claimed_status(feed.feed_id, feed.query_id, timestamps_lis, handler_func))

        if not len(calls):
            return None, error_status("No getRewardClaimStatusList Calls to assemble")

        reward_claimed_status_resp, status = await self.multi_call(calls, success=True)

        if not status.ok:
            return None, status

        if not reward_claimed_status_resp:
            return None, error_status("No response returned from getRewardClaimStatusList batch multicall")

        return reward_claimed_status_resp, status

    async def currentfeeds_multiple_values_before(
        self, datafeed: DataFeed[Any], month_old_timestamp: int, now_timestamp: int
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
            ('values_array, b'query_id'): (values in bytes),
            ('timestamps_array', b'query_id'): (timestamps)
        }
        """
        query_id = datafeed.query.query_id
        calls = [
            self.get_current_feeds(query_id=query_id),
            self.get_multiple_values_before(
                query_id=query_id, now_timestamp=now_timestamp, max_age=month_old_timestamp
            ),
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
            values = resp[("values_array", query_id)]
            timestamps = resp[("timestamps_array", query_id)]

            # short circuit the loop since None means failed response and can't calculate tip accurately
            if values is None:
                note = "getMultipleValuesBefore call failed"
                return None, error_status(note)

            current_value = values[-1] if values else b""
            current_value_timestamp = timestamps[-1] if timestamps else 0
            values_lis = values[:-1]
            timestamps_lis = timestamps[:-1]
            timestamps_values_list = list(map(Values, values_lis, timestamps_lis))

            feed = QueryIdandFeedDetails(
                feed_id=feed_id,
                query_id=query_id,
                query_data=datafeed.query.query_data,
                current_queryid_value=current_value,
                current_value_timestamp=current_value_timestamp,
                queryid_timestamps_values_list=timestamps_values_list,
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
        calls = [self.get_data_feed(feed_id=feed.feed_id) for feed in feeds]

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

        return feeds, status
