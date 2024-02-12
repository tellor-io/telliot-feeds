from typing import Any
from typing import Optional
from typing import Tuple

from telliot_core.tellor.tellorflex.autopay import TellorFlexAutopayContract
from telliot_core.utils.timestamp import TimeStamp

from telliot_feeds.datafeed import DataFeed
from telliot_feeds.reporters.tips.listener.funded_feeds import FundedFeeds
from telliot_feeds.reporters.tips.listener.one_time_tips import get_funded_one_time_tips
from telliot_feeds.reporters.tips.listener.utils import get_sorted_tips
from telliot_feeds.reporters.tips.multicall_functions.multicall_autopay import MulticallAutopay
from telliot_feeds.utils.log import get_logger
from telliot_feeds.utils.query_search_utils import feed_from_catalog_feeds
from telliot_feeds.utils.query_search_utils import feed_in_feed_builder_mapping
from telliot_feeds.utils.query_search_utils import get_query_from_qtyp_name


logger = get_logger(__name__)


# suggest a feed here not a query tag, because build feed portion
# or check both mappings for type
async def get_feed_and_tip(
    autopay: TellorFlexAutopayContract, skip_manual_feeds: bool, current_timestamp: Optional[TimeStamp] = None
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

    funded_feeds = FundedFeeds(autopay=autopay, multi_call=multi_call)

    feed_tips = await funded_feeds.querydata_and_tip(current_time=current_timestamp)
    onetime_tips = await get_funded_one_time_tips(autopay=autopay)

    if not feed_tips and not onetime_tips:
        logger.info("No tips available in autopay")
        return None, None

    sorted_tips = get_sorted_tips(feed_tips, onetime_tips)
    for suggestion in sorted_tips:
        query_data, tip_amount = suggestion
        if tip_amount == 0:
            return None, None

        datafeed = feed_from_catalog_feeds(query_data)

        if datafeed is None:
            # TODO: add skip manual feed flag to make optional; currently skips all manual feeds
            datafeed = feed_in_feed_builder_mapping(query_data, skip_manual_feeds=skip_manual_feeds)

        if datafeed is not None:
            query = get_query_from_qtyp_name(query_data)
            datafeed.query = query  # type: ignore
            for param in datafeed.query.__dict__.keys():
                val = getattr(query, param)
                setattr(datafeed.source, param, val)
            break

    if datafeed is None:
        return None, None
    return datafeed, tip_amount
