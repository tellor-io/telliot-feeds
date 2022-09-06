from telliot_core.tellor.tellorflex.autopay import TellorFlexAutopayContract
from telliot_feeds.reporters.tip_listener.tip_listener_filter import TipListenerFilter
from telliot_core.utils.timestamp import TimeStamp
from telliot_feeds.reporters.tip_listener.utils import QueryIdTimestamps
from telliot_feeds.reporters.tip_listener.utils import QueryIdValuesInfo
from multicall import Call
from multicall import Multicall
from typing import Dict
from typing import Any
from typing import Tuple
from typing import List
from collections import defaultdict


class AutopayMulticalls(TipListenerFilter):
    """
        Getter of each query_ids:
        - current_values
        - getIndexForDataBefore - Now
        - getIndexForDataBefore - 1 MONTH ago
        - getTimestampbyQueryIdandIndex [] from to historical timestamp reported
        - getRewardClaimedStatus
        """
    def __init__(self, autopay: TellorFlexAutopayContract) -> None:
        self.autopay = autopay
        self.ids: Dict[bytes, bytes] = {}
        self.w3 = self.autopay.node._web3

    def concatenate_calls(
        self, *args: tuple, func_sig: str, helper_func: Any = None, **kwargs: Dict[str, Any]
    ) -> List[Call]:
        """Concatenate Call lists to submit a batch contract call

        Args:
        - func_sig: function signature
        - helper_func: helper function that handles call response

        Return: List of calls
        """
        query_ids = set(self.ids[query_id] for query_id in self.ids)
        calls: List[Call] = [
            Call(
                self.autopay.address,
                [func_sig, query_id] + list(kwargs.values()),  # type: ignore
                [[(arg, query_id.hex()), helper_func] for arg in args] if args else [[query_id.hex(), helper_func]]
            )
            for query_id in query_ids
        ]
        return calls

    def get_data_before_calls(self, now_timestamp: TimeStamp) -> List[Call]:
        """concatenate getDataBefore autopay Call object

        Return: list of Call objects for batch call
        """
        return self.concatenate_calls(
            "value", "timestamp", func_sig="getDataBefore(bytes32,uint256)(bytes,uint256)",
            param1=now_timestamp
        )

    def get_index_for_data_before_now(self, now_timestamp: TimeStamp) -> List[Call]:
        """concatenate getIndexForDataBefore autopay Call object for current timestamp

        Return: list of Call objects for batch call
        """
        return self.concatenate_calls(
            "current", "now_index", func_sig="getIndexForDataBefore(bytes32,uint256)(bool,uint256)",
            param1=now_timestamp
        )

    def get_index_for_data_before_month(self, month_old: TimeStamp) -> List[Call]:
        """concatenate getIndexForDataBefore autopay Call object for month old timestamp

        Return: list of Call objects for batch call
        """
        return self.concatenate_calls(
            "month_old", "month_old_index", func_sig="getIndexForDataBefore(bytes32,uint256)(bool,uint256)",
            param1=month_old
        )

    def get_timestamp_by_query_id_and_index(self, index: int) -> List[Call]:
        """concatenate getTimestampbyQueryIdandIndex autopay Call object to fetch
        a list of timestamps for the past month

        Return: list of Call objects for batch call
        """
        return self.concatenate_calls(
            index, func_sig="getTimestampbyQueryIdandIndex(bytes32,uint256)(uint256)",
            param1=index  # type: ignore
        )

    def get_reward_claimed_status(self, objects: List[QueryIdTimestamps]) -> List[Call]:
        """Concatenate Call object for a batch multicall of getRewardClaimStatusList
        to fetch claim status of each timestamp

        Return: a list of Call objects for batch call
        """
        map_queryid_obj = {obj.query_id: obj for obj in objects}
        func_sig = "getRewardClaimStatusList(bytes32,bytes32,uint256[])(bool[])"
        calls: List[Call] = [
            Call(
                self.autopay.address,
                [func_sig, feed_id, query_id, map_queryid_obj[query_id.hex()].timestamps],
                [[(feed_id.hex(), query_id.hex()), lambda res: len(list(filter((True).__ne__, res)))]]
            )
            for feed_id, query_id in self.ids.items()
        ]
        return calls

    async def multi_call(self, calls: List[Call]) -> Dict[str, Any]:
        multi_call = Multicall(calls=calls, _w3=self.autopay.node._web3, require_success=False)
        data: Dict[str, Any] = await multi_call.coroutine()
        return data

    async def batch_diverse(self, month_old_timestamp: int, now_timestamp: int) -> List[QueryIdValuesInfo]:
        """Batch call two functions (getDataBefore,getIndexForDataBefore)

        Args:
        - now_timestamp: current time in unix timestamps
        - month_old_timestamp: now_timestamp - 2_592_000

        Return: a list of QueryIdTimestamps
        to be used in the next batch call that fetches a list of timestamps for each queryId
        """
        print(now_timestamp, "timestamp")
        data_before = self.get_data_before_calls(now_timestamp=now_timestamp)
        get_index_for_data_before_now = self.get_index_for_data_before_now(now_timestamp=now_timestamp)
        get_index_for_data_before_month = self.get_index_for_data_before_month(month_old=month_old_timestamp)

        calls = data_before + get_index_for_data_before_now + get_index_for_data_before_month
        print("batchone length ", len(calls))
        # error handle this
        resp = await self.multi_call(calls)
        # filter data out here
        clean_resp = _filter_batch_result(resp)
        batch_one_results = [QueryIdValuesInfo(*clean_resp[key], key) for key in clean_resp]
        return batch_one_results

    async def batch_timestamps_list(self, query_id_info: List[QueryIdValuesInfo]) -> List[QueryIdTimestamps]:
        """Batch call getTimestampbyQueryIdandIndex to fetch a list of timestamps for each query id

        Args:
        - query_id_info: a list of QueryIdValuesInfo object

        Return: a list of QueryIdTimestamps object that carries query id and its month long timestamps list
        """

        calls = []
        for obj in query_id_info:
            for j in range(obj.month_old_index, obj.now_index + 1):
                calls += self.get_timestamp_by_query_id_and_index(j)
        print("batchtwo length ", len(calls))
        # error handle
        resp = await self.multi_call(calls)
        clean_resp = _filter_batch_result(resp)
        batch_timestamps_list_results = [QueryIdTimestamps(key, clean_resp[key]) for key in clean_resp]
        # filter
        print(batch_timestamps_list_results, "batch_timestamps_list_results")
        return batch_timestamps_list_results

    async def batch_rewards_claimed(self, batch_timestamps_list: List[QueryIdTimestamps]) -> Dict[Tuple[str, str], int]:
        """Batch call getRewardClaimStatusList

        Args:
        - batch_timestamps_list: list QueryIdTimestamps that carry a list of timestamps

        Return: dict with count of unclaimed timestamps
        """
        calls = await self.get_reward_claimed_status(batch_timestamps_list)
        reward_claimed_status_resp = await self.multi_call(calls)
        print(reward_claimed_status_resp)

        return reward_claimed_status_resp

    # async def batch_call(
    #     self,
    #     now_timestamp,
    #     month_old_timestamp
    # ) -> Tuple[List[QueryIdValuesInfo], List[Dict[Tuple[str, str], int]]]:
    #     """Trigger multicalls"""
    #     print("now", now_timestamp)
    #     batch_one = await self.batch_diverse(now_timestamp=now_timestamp, month_old_timestamp=month_old_timestamp)
    #     print(batch_one, "batch_one")
    #     batch_two = await self.batch_timestamps_list(query_id_info=batch_one)
    #     print(batch_two, "batch_two")
    #     batch_three = await self.batch_rewards_claimed(batch_timestamps_list=batch_two)
    #     print(batch_three)
    #     return batch_one, batch_three


def _filter_batch_result(data: dict) -> defaultdict[Any, list]:
    from collections import defaultdict
    mapping = defaultdict(list)
    results = defaultdict(list)

    for k in data:
        mapping[k[1]].append(k)
    for query_id in mapping:
        for val in mapping[query_id]:
            value = data[val]
            results[query_id].append(value)

    return results
