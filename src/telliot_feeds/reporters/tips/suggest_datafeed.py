from typing import Any
from typing import Optional
from typing import Tuple

from telliot_core.tellor.tellorflex.autopay import TellorFlexAutopayContract

from telliot_feeds.datafeed import DataFeed
from telliot_feeds.reporters.tips.funded_feeds.funded_feeds import FundedFeeds
from telliot_feeds.reporters.tips.funded_feeds.multicall_autopay import MulticallAutopay
from telliot_feeds.reporters.tips.listener.funded_feeds_filter import FundedFeedFilter
from telliot_feeds.reporters.tips.listener.utils import get_sorted_tips
from telliot_feeds.reporters.tips.onetime.one_time_tips import OneTimeTips
from telliot_feeds.utils.log import get_logger


logger = get_logger(__name__)


# suggest a feed here not a query tag, because build feed portion
# or check both mappings for type
async def feed_suggestion(
    autopay: TellorFlexAutopayContract,
) -> Optional[Tuple[Optional[DataFeed[Any]], Optional[int]]]:
    chain_id = autopay.node.chain_id

    if chain_id in (137, 80001, 69, 1666600000, 1666700000, 421611, 42161):
        assert isinstance(autopay, TellorFlexAutopayContract)

    multi_call = MulticallAutopay()
    feed_filter = FundedFeedFilter()

    one_time_tips = OneTimeTips(autopay=autopay)
    funded_feeds = FundedFeeds(autopay=autopay, multi_call=multi_call, feed_filter=feed_filter)

    feed_tips = await funded_feeds.querydata_and_tip()
    onetime_tips = await one_time_tips.get_funded_one_time_tips()

    if not feed_tips and not onetime_tips:
        logger.info("No tips available in autopay")
        return None, None

    sorted_tips = get_sorted_tips(feed_tips, onetime_tips)
    for suggestion in sorted_tips:
        query_data = suggestion[0]
        tip_amount = suggestion[1]

        datafeed = feed_filter.qtag_in_feed_mapping(query_data)
        if datafeed is None:
            datafeed = feed_filter.qtype_in_feed_builder_mapping(query_data)

        if datafeed is not None:
            query = feed_filter.get_query_from_qtyp_name(query_data)
            datafeed.query = query
            break

    return datafeed, tip_amount
