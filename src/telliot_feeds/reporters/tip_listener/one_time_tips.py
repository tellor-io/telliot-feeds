"""Single tip feed suggeestion"""
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union

from telliot_core.tellor.tellorflex.autopay import TellorFlexAutopayContract

from telliot_feeds.reporters.tip_listener.tip_listener_filter import TipListenerFilter
from telliot_feeds.utils.log import get_logger

logger = get_logger(__name__)


class OneTimeTips(TipListenerFilter):
    def __init__(self, autopay: TellorFlexAutopayContract) -> None:
        self.autopay = autopay

    async def get_one_time_tip_funded_queries(self) -> Optional[Dict[bytes, int]]:
        """Trigger autopay call and filter response data

        Return: list of tuples of only query data and tips
        that exist in telliot registry
        """
        onetime_tips: Optional[List[Tuple[Union[bytes, int]]]]
        onetime_tips, status = await self.autopay.read("getFundedSingleTipsInfo")

        if not status.ok or not onetime_tips:
            logger.info("No one time tip funded queries available")
            return None

        for (query_data, reward) in list(onetime_tips):
            # add error catch here
            qtype_name = self.decode_typ_name(query_data=query_data)  # type: ignore
            if not self.qtype_name_in_registry(qtyp_name=qtype_name):
                onetime_tips.remove((query_data, reward))  # type: ignore

        single_tips = {query_data: tip for (query_data, tip) in onetime_tips}  # type: ignore
        return single_tips
