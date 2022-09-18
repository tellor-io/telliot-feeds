from typing import Any
from typing import Callable
from typing import Optional

from multicall import Call
from telliot_core.utils.timestamp import TimeStamp

from telliot_feeds.reporters.tips.funded_feeds.multicall_autopay import MulticallAutopay


class CallFunctionSingle(MulticallAutopay):
    """Assemble the autopay function call objects that will be called via multicall in batch"""

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
