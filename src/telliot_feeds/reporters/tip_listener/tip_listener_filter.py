import math
from typing import Any
from typing import Dict
from typing import List
from typing import Tuple

from clamfig.base import Registry
from eth_abi import decode_single
from eth_abi import encode_single
from eth_utils.conversions import to_bytes
from telliot_core.utils.response import ResponseStatus

from telliot_feeds.reporters.tip_listener.tip_listener import TipListener
from telliot_feeds.reporters.tip_listener.utils import Feed


class TipListenerFilter(TipListener):
    async def autopay_function_call(self, func_name: str, **kwargs: Dict[Any, str]) -> Tuple[Any, ResponseStatus]:
        data, status = await self.autopay.read(func_name, **kwargs)
        return data, status

    def decode_typ_name(self, query_data: bytes) -> str:
        try:
            qtype_name = decode_single("(string,bytes)", query_data)[0]
        except OverflowError:
            # string query for some reason encoding isn't the same as the others
            import ast

            qtype_name = ast.literal_eval(query_data.decode("utf-8"))["type"]
        return qtype_name

    def qtype_name_in_registry(self, qtyp_name: str) -> bool:
        if qtyp_name not in Registry.registry:
            return False
        return True

    def generate_ids(self, feed: Feed) -> Tuple[bytes, bytes]:
        """Hash feed details to generate query id and feed id

        Return:
        - query_id: keccak(query_data)
        - feed_id: keccak(abi.encode(queryId,reward,startTime,interval,window,priceThreshold,rewardIncreasePerSecond)
        """

        w3 = self.autopay.node._web3
        feed_details = feed.details
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
    ) -> bool:
        """
        Calculates to check if timestamp(timestamp_to_check) is first in window

        Return: bool
        """
        # Number of intervals since start time
        num_intervals = math.floor((timestamp_to_check - feed_start_timestamp) / feed_interval)
        # Start time of latest submission window
        current_window_start = feed_start_timestamp + (feed_interval * num_intervals)
        eligible = [(timestamp_to_check - current_window_start) < feed_window, timestamp_before < current_window_start]
        return all(eligible)

    def get_max_tip(feed: List[Tuple[bytes, int]]) -> List[Tuple[bytes, int]]:
        return max(feed, key=lambda item: item[1])
