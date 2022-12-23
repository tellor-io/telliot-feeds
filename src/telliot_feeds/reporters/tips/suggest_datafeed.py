from typing import Any
from typing import Optional
from typing import Tuple

from telliot_core.tellor.tellorflex.autopay import TellorFlexAutopayContract
from telliot_core.utils.timestamp import TimeStamp

from telliot_feeds.datafeed import DataFeed
from telliot_feeds.reporters.tips.listener.funded_feeds import FundedFeeds
from telliot_feeds.reporters.tips.listener.one_time_tips import get_funded_one_time_tips
from telliot_feeds.reporters.tips.listener.tip_listener_filter import TipListenerFilter
from telliot_feeds.reporters.tips.listener.utils import get_sorted_tips
from telliot_feeds.reporters.tips.multicall_functions.multicall_autopay import MulticallAutopay
from telliot_feeds.utils.log import get_logger


logger = get_logger(__name__)


# suggest a feed here not a query tag, because build feed portion
# or check both mappings for type
async def get_feed_and_tip(
    autopay: TellorFlexAutopayContract, current_timestamp: Optional[TimeStamp] = None
) -> Optional[Tuple[Optional[DataFeed[Any]], Optional[int]]]:
    """Fetch feeds with their tip and filter to get a feed suggestion with the max tip

    Args:
    - autopay contract object
    - current_timestamp

    Returns:
    - tuple of feed and tip amount
    """
    if current_timestamp is None:
        current_timestamp = TimeStamp.now().ts

    multi_call = MulticallAutopay()
    listener_filter = TipListenerFilter()

    funded_feeds = FundedFeeds(
        autopay=autopay, multi_call=multi_call, listener_filter=listener_filter.qtype_name_in_registry
    )

    feed_tips = await funded_feeds.querydata_and_tip(current_time=current_timestamp)
    onetime_tips = await get_funded_one_time_tips(
        autopay=autopay, listener_filter=listener_filter.qtype_name_in_registry
    )

    if not feed_tips and not onetime_tips:
        logger.info("No tips available in autopay")
        return None, None

    sorted_tips = get_sorted_tips(feed_tips, onetime_tips)
    for suggestion in sorted_tips:
        query_data, tip_amount = suggestion
        if tip_amount == 0:
            return None, None

        datafeed = listener_filter.qtag_in_feed_mapping(query_data)

        if datafeed is None:
            datafeed = listener_filter.qtype_in_feed_builder_mapping(query_data)

        if datafeed is not None:
            query = listener_filter.get_query_from_qtyp_name(query_data)
            datafeed.query = query  # type: ignore
            for param in datafeed.query.__dict__.keys():
                val = getattr(query, param)
                setattr(datafeed.source, param, val)
            break

    return datafeed, tip_amount
