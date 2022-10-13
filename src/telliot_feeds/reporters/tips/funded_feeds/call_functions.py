from typing import Any
from typing import Callable
from typing import Optional

from multicall import Call
from telliot_core.tellor.tellorflex.autopay import TellorFlexAutopayContract

from telliot_feeds.reporters.tips.listener.assemble_call import AssembleCall


class CallFunctions(AssembleCall):
    """
    Assemble Call for autopay functions:
    - getDataBefore
    - getIndexForDataBefore - Now
    - getIndexForDataBefore - 1 MONTH ago
    - getTimestampbyQueryIdandIndex [] from to historical timestamp reported
    - getRewardClaimedStatus
    """

    def __init__(self) -> None:
        self.autopay: TellorFlexAutopayContract

    def get_reward_claimed_status(
        self,
        feed_id: bytes,
        query_id: bytes,
        timestamps: Optional[list[int]],
        handler_function: Optional[Callable[..., Any]] = None,
    ) -> Call:
        """getRewardClaimStatusList autopay Call object for list of timestamps

        Args:
        - feed_id
        - query_id
        - timestamps: list of timestamps
        - handler_function: function to interpret contract reponse (optional)

        Return: Call object
        example return from this call:
        >>> {(b'feed_id', b'query_id'): [True, False, True,]}
        """
        return self.assemble_call_object(
            func_sig="getRewardClaimStatusList(bytes32,bytes32,uint256[])(bool[])",
            returns=[[(feed_id, query_id), handler_function]],
            feed_id=feed_id,
            query_id=query_id,
            param3=timestamps,
        )

    def get_current_feeds(self, query_id: bytes, handler_function: Optional[Callable[..., Any]] = None) -> Call:
        """getCurrentFeeds autopay Call object for a query id

        Args:
        - query_id
        - handler_function: function to interpret contract reponse (optional)

        Return: Call object
        example return from this call:
        >>> {b'query_id': [b'feed_id',]}
        """
        return self.assemble_call_object(
            func_sig="getCurrentFeeds(bytes32)(bytes32[])",
            returns=[
                [query_id, handler_function],
            ],
            query_id=query_id,
        )

    def get_data_feed(self, feed_id: bytes, handler_function: Optional[Callable[..., Any]] = None) -> Call:
        """getDataFeed autopay Call object for month old timestamp

        Args:
        - feed_id
        - handler_function: function to interpret contract reponse (optional)

        Return: Call object
        example return from this call:
        >>> {b'feed_id': (reward, balance, startTime, interval, window, priceThreshold, rewardIncreasePerSecond,
        feedsWithFundingIndex)}
        """
        return self.assemble_call_object(
            func_sig="getDataFeed(bytes32)((uint256,uint256,uint256,uint256,uint256,uint256,uint256))",
            returns=[
                [feed_id, handler_function],
            ],
            feed_id=feed_id,
        )

    def get_multiple_values_before(
        self,
        query_id: bytes,
        now_timestamp: int,
        max_age: int,
        max_count: int = 40_000,
        handler_function: Optional[Callable[..., Any]] = None,
    ) -> Call:
        """getMultipleValuesBefore autopay Call object for getting a month worth of values
        for a query id

        Args:
        - query_id
        - now_timestamp
        - max_age: the maximum number of seconds before the now_timestamp to search for values
        now_timestamp - 2_592_000 (one month)
        - max_count: the maximum number of values to return
        - handler_function: function to interpret contract reponse (optional)

        Return: Call object
        example return from this call:
        >>> {(values_array, b'query_id'): ["values"] (timestamps_array, b'query_id'): [timestamps]}
        """
        return self.assemble_call_object(
            func_sig="getMultipleValuesBefore(bytes32,uint256,uint256,uint256)(bytes[],uint256[])",
            returns=[
                [("values_array", query_id), handler_function],
                [("timestamps_array", query_id), handler_function],
            ],
            query_id=query_id,
            param1=now_timestamp,
            param2=max_age,
            param3=max_count,
        )
