from typing import Any
from typing import Callable
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

from eth_utils.conversions import to_bytes
from multicall import Call
from multicall import Multicall
from telliot_core.tellor.tellorflex.autopay import TellorFlexAutopayContract
from telliot_core.utils.timestamp import TimeStamp

from telliot_feeds.reporters.tip_listener.utils_tip_listener import filter_batch_result
from telliot_feeds.reporters.tip_listener.utils_tip_listener import FullFeedQueryDetails


class AutopayMulticalls:
    """
    Getter of:
    - current_values
    - getIndexForDataBefore - Now
    - getIndexForDataBefore - 1 MONTH ago
    - getTimestampbyQueryIdandIndex [] from to historical timestamp reported
    - getRewardClaimedStatus
    """

    def __init__(self) -> None:
        self.autopay: TellorFlexAutopayContract

    async def multi_call(self, calls: List[Call], success: bool = True) -> Dict[Any, Any]:
        """Make multi-call given a list of Calls

        Arg:
        - calls: list of Call objects
        - success: boolean, setting to false will handle any contract logic errors

        Return:
        - dictionary of of Any type key, could be tuple, string, or number
        """
        multi_call = Multicall(calls=calls, _w3=self.autopay.node._web3, require_success=success)
        data: Dict[Any, Any] = await multi_call.coroutine()
        return data

    def single_autopay_function_call(
        self, *args: Any, func_sig: str, handler_func: Optional[Callable[[Any], Any]] = None, **kwargs: Any
    ) -> Call:
        """Assemble a single Call object to use in a batch call through multicall

        Args:
        - *args: key identifier to use in the dictionary to identify the reponse from the multicall
        and avoid data deletion by overwriting the dictionary
        - func_sig: the function to call with params' types and return type
        i.e. "funcsig(paramtype1, paramtype2)(returntype1)"
        - handler_func: optional function to handle call response, default None
        - *kwargs: setting the query_id and feed_id (don't include feed_id if args included)

        Return: Call object
        """
        return Call(
            target=self.autopay.address,
            function=[func_sig] + list(kwargs.values()),
            # key for dictionary will be tuple if a Call has multiple functions with the same param
            # dictionaries require unique keys and to avoid overwriting data use tuple with differentiating
            # descriptor item in tuple
            returns=[[(arg, kwargs["query_id"]), handler_func] for arg in args]
            if args
            else [[(kwargs["feed_id"], kwargs["query_id"]), handler_func]],
        )

    def get_data_before_calls(self, query_id: bytes, now_timestamp: TimeStamp) -> Call:
        """concatenate getDataBefore autopay Call object for list of query ids

        Return: list of Call objects for batch call
        """
        return self.single_autopay_function_call(
            "current_value",
            "current_value_timestamp",
            func_sig="getDataBefore(bytes32,uint256)(bytes,uint256)",
            query_id=query_id,
            param1=now_timestamp,
        )

    def get_index_for_data_before_now(self, query_id: bytes, now_timestamp: TimeStamp) -> Call:
        """concatenate getIndexForDataBefore autopay Call object for current timestamp

        Return: list of Call objects for batch call
        """
        return self.single_autopay_function_call(
            "current_status",
            "current_value_index",
            func_sig="getIndexForDataBefore(bytes32,uint256)(bool,uint256)",
            query_id=query_id,
            param2=now_timestamp,
        )

    def get_index_for_data_before_month(self, query_id: bytes, month_old: TimeStamp) -> Call:
        """concatenate getIndexForDataBefore autopay Call object for month old timestamp

        Return: list of Call objects for batch call
        """
        return self.single_autopay_function_call(
            "month_old_status",
            "month_old_index",
            func_sig="getIndexForDataBefore(bytes32,uint256)(bool,uint256)",
            query_id=query_id,
            param2=month_old,
        )

    def get_timestamp_by_query_id_and_index(self, query_id: bytes, index: int) -> Call:
        """concatenate getTimestampbyQueryIdandIndex autopay Call object to fetch
        a list of timestamps for the past month

        Return: list of Call objects for batch call
        """
        # {queryid: (startingIndex,endingIndex)}
        return self.single_autopay_function_call(
            index,
            func_sig="getTimestampbyQueryIdandIndex(bytes32,uint256)(uint256)",
            query_id=query_id,
            param1=index,
        )

    def get_reward_claimed_status(
        self, feed_id: Optional[bytes], query_id: bytes, timestamps: Optional[List[int]]
    ) -> Call:
        """Concatenate Call object for a batch multicall of getRewardClaimStatusList
        to fetch claim status of each timestamp

        Return: a list of Call objects for batch call
        """

        def handler_func(res: Any) -> int:
            return len(list(filter((True).__ne__, res)))

        return self.single_autopay_function_call(
            func_sig="getRewardClaimStatusList(bytes32,bytes32,uint256[])(bool[])",
            handler_func=handler_func,
            feed_id=feed_id,
            query_id=query_id,
            param3=timestamps,
        )

    # make the calls
    async def timestamp_index_and_current_values_call(
        self, feeds: List[FullFeedQueryDetails], month_old_timestamp: int, now_timestamp: int
    ) -> List[FullFeedQueryDetails]:
        """Batch call two functions (getDataBefore,getIndexForDataBefore)

        Args:
        - now_timestamp: current time in unix timestamps
        - month_old_timestamp: now_timestamp - 2_592_000

        Return: a list of FullFeedQueryDetails
        to be used in the next batch call that fetches a list of timestamps for each queryId
        """
        calls = []
        for i in feeds:
            calls += [
                self.get_data_before_calls(query_id=i.query_id, now_timestamp=now_timestamp),
                self.get_index_for_data_before_now(query_id=i.query_id, now_timestamp=now_timestamp),
                self.get_index_for_data_before_month(query_id=i.query_id, month_old=month_old_timestamp),
            ]
        if len(calls) < 1:
            print("No calls concatenated to be called for batch diverse functions")
            return feeds

        # success equal to False handles any contract logic errors and return empty {}
        resp = await self.multi_call(calls, success=False)

        if not resp:
            print("No response returned for batch current values and indices function calls")
            return feeds

        # filter data out here
        for i in feeds:
            # autopay contract returns 0 or b'' if no current value and 0 if no month old index
            i.current_value_timestamp = resp[("current_value_timestamp", i.query_id)]
            i.current_value = resp[("current_value", i.query_id)]
            i.current_value_index = resp[("current_value_index", i.query_id)]
            i.month_old_index = resp[("month_old_index", i.query_id)]

        return feeds

    async def timestamps_list_call(self, feeds: List[FullFeedQueryDetails]) -> Optional[List[FullFeedQueryDetails]]:
        """Batch call getTimestampbyQueryIdandIndex to fetch a list of timestamps for each query id

        Args:
        - feeds: a list of FullFeedQueryDetails object

        Return: a list of FullFeedQueryDetails object that carries query id and its month long timestamps list
        """
        calls = []
        for detail in feeds:
            for i in range(detail.month_old_index, detail.current_value_index):
                calls.append(self.get_timestamp_by_query_id_and_index(to_bytes(hexstr=detail.query_id), index=i))

        if len(calls) < 0:
            # if no calls concated then return feeds w/out assigning timestamps list
            return None

        resp = await self.multi_call(calls)

        if not resp:
            # if multicall response {} empty then return feeds w/out assigning timestamps list
            return None

        clean_resp = filter_batch_result(resp)

        for feed in feeds:
            feed.queryId_timestamps_list = clean_resp[feed.query_id]

        return feeds

    async def rewards_claimed_status_call(
        self, feeds: List[FullFeedQueryDetails]
    ) -> Optional[Dict[Tuple[Optional[bytes], Optional[bytes]], int]]:
        """Batch call getRewardClaimStatusList

        Args:
        - feeds: list FullFeedQueryDetails that carry a list of timestamps

        Return: dict with count of unclaimed timestamps
        """
        calls = []
        for i in feeds:
            calls.append(self.get_reward_claimed_status(i.feed_id, i.query_id, i.queryId_timestamps_list))

        reward_claimed_status_resp = await self.multi_call(calls)
        if not reward_claimed_status_resp:
            print("rewards claim status call return {}")
            return None

        return reward_claimed_status_resp
