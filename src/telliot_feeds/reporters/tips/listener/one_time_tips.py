"""Single tip feed suggeestion"""
from typing import Optional

from telliot_core.tellor.tellorflex.autopay import TellorFlexAutopayContract

from telliot_feeds.utils.log import get_logger
from telliot_feeds.utils.query_search_utils import qtype_name_in_registry

logger = get_logger(__name__)


async def get_funded_one_time_tips(autopay: TellorFlexAutopayContract) -> Optional[dict[bytes, int]]:
    """Trigger autopay call and filter response data

    Return: list of tuples of only query data and tips
    that exist in telliot registry
    """
    onetime_tips: Optional[list[tuple[bytes, int]]]
    onetime_tips, status = await autopay.read("getFundedSingleTipsInfo")

    if not status.ok or not onetime_tips:
        logger.info("No one time tip funded queries available")
        return None

    for (query_data, reward) in list(onetime_tips):
        if query_data == b"":
            onetime_tips.remove((query_data, reward))
            continue

        if not qtype_name_in_registry(query_data):
            onetime_tips.remove((query_data, reward))

    single_tips = {query_data: reward for (query_data, reward) in onetime_tips}

    return single_tips
