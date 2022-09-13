"""Single tip feed suggeestion"""
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

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
        onetime_tips: Optional[List[Tuple[bytes, int]]]
        onetime_tips, status = await self.autopay.read("getFundedSingleTipsInfo")

        if not status.ok or not onetime_tips:
            logger.info("No one time tip funded queries available")
            return None

        for (query_data, reward) in list(onetime_tips):
            if query_data == b"":
                print("Bad query data response")
                onetime_tips.remove((query_data, reward))
                continue

            qtype_name = self.decode_typ_name(qdata=query_data)
            if not self.qtype_name_in_registry(qtyp_name=qtype_name):
                onetime_tips.remove((query_data, reward))

        single_tips = {query_data: reward for (query_data, reward) in onetime_tips}
        return single_tips
