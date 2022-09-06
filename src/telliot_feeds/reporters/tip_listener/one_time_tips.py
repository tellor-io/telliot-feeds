"""Single tip feed suggeestion"""
from typing import List
from typing import Optional

from telliot_feeds.reporters.tip_listener.tip_listener_filter import TipListenerFilter
from telliot_feeds.reporters.tip_listener.utils import OneTimeTipDetails
from telliot_feeds.utils.log import get_logger

logger = get_logger(__name__)


class OneTimeTips(TipListenerFilter):

    feeds = None

    async def get_one_time_tip_funded_queries(self) -> Optional[List[OneTimeTipDetails]]:
        """Trigger autopay call and filter response data

        :return: list of tuples of only query data and tips
        that exist in telliot registry
        """
        onetime_tips: Optional[List[OneTimeTipDetails]]
        onetime_tips, status = await self.autopay_function_call("getFundedSingleTipsInfo")

        if not status.ok or not onetime_tips:
            logger.info("No one time tip funded queries available")
            return None

        for (query_data, reward) in list(onetime_tips):
            # add error catch here
            qtype_name = self.decode_typ_name(query_data=query_data)  # type: ignore
            if not self.qtype_name_in_registry(qtyp_name=qtype_name):
                onetime_tips.remove((query_data, reward))  # type: ignore

        return onetime_tips
