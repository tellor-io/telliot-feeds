from typing import Any
from typing import Callable
from typing import List
from typing import Optional

from multicall import Call
from telliot_core.tellor.tellorflex.autopay import TellorFlexAutopayContract
from telliot_core.utils.timestamp import TimeStamp

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

    def get_data_before(
        self, query_id: bytes, now_timestamp: TimeStamp, handler_function: Optional[Callable[..., Any]] = None
    ) -> Call:
        """getDataBefore autopay Call object for a query_id

        Args:
        - query_id
        - now_timestamp
        - handler_function: function to interpret contract reponse (optional)

        Return: Call object
        example return from this call:
        >>> {("current_value", query_id): b'value', ("current_value_timestamp", b'query_id'): 123456}
        """
        return self.assemble_call_object(
            func_sig="getDataBefore(bytes32,uint256)(bytes,uint256)",
            returns=[
                [("current_value", query_id), handler_function],
                [("current_value_timestamp", query_id), handler_function],
            ],
            query_id=query_id,
            param1=now_timestamp,
        )

    def get_index_for_data_before_now(
        self, query_id: bytes, now_timestamp: TimeStamp, handler_function: Optional[Callable[..., Any]] = None
    ) -> Call:
        """getIndexForDataBefore autopay Call object for current timestamp

        Args:
        - query_id
        - now_timestamp
        - handler_function: function to interpret contract reponse (optional)

        Return: Call object
        example return from this call:
        >>> {("current_status", b'query_id'): True, ("current_value_index", b'query_id'): 1}
        """
        return self.assemble_call_object(
            func_sig="getIndexForDataBefore(bytes32,uint256)(bool,uint256)",
            returns=[
                [("current_status", query_id), handler_function],
                [("current_value_index", query_id), handler_function],
            ],
            query_id=query_id,
            param2=now_timestamp,
        )

    def get_index_for_data_before_month(
        self, query_id: bytes, month_old: TimeStamp, handler_function: Optional[Callable[..., Any]] = None
    ) -> Call:
        """getIndexForDataBefore autopay Call object for month old timestamp

        Args:
        - query_id
        - one_month_old
        - handler_function: function to interpret contract reponse (optional)

        Return: Call object
        example return from this call:
        >>> {("month_old_status", b'query_id'): True, ("month_old_index", b'query_id'): 1}
        """
        return self.assemble_call_object(
            func_sig="getIndexForDataBefore(bytes32,uint256)(bool,uint256)",
            returns=[
                [("month_old_status", query_id), handler_function],
                [("month_old_index", query_id), handler_function],
            ],
            query_id=query_id,
            param2=month_old,
        )

    def get_timestamp_by_query_id_and_index(
        self, query_id: bytes, index: int, handler_function: Optional[Callable[..., Any]] = None
    ) -> Call:
        """getTimestampbyQueryIdandIndex autopay Call object

        Args:
        - query_id
        - index
        - handler_function: function to interpret contract reponse (optional)

        Return: list of Call objects for batch call
        """
        # {(index, b'query_id): 1234}
        return self.assemble_call_object(
            func_sig="getTimestampbyQueryIdandIndex(bytes32,uint256)(uint256)",
            returns=[[(index, query_id), handler_function]],
            query_id=query_id,
            param1=index,
        )

    def get_reward_claimed_status(
        self,
        feed_id: bytes,
        query_id: bytes,
        timestamps: Optional[List[int]],
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
