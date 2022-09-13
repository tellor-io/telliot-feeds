from typing import Any
from typing import Optional
from typing import Tuple

from telliot_core.tellor.tellorflex.autopay import TellorFlexAutopayContract

from telliot_feeds.datafeed import DataFeed
from telliot_feeds.feeds import CATALOG_FEEDS
from telliot_feeds.feeds import DATAFEED_BUILDER_MAPPING
from telliot_feeds.feeds import LEGACY_DATAFEEDS
from telliot_feeds.reporters.tip_listener.autopay_multicalls import AutopayMulticalls
from telliot_feeds.reporters.tip_listener.funded_feeds import FundedFeeds
from telliot_feeds.reporters.tip_listener.funded_feeds_filter import FundedFeedFilter
from telliot_feeds.reporters.tip_listener.one_time_tips import OneTimeTips
from telliot_feeds.reporters.tip_listener.utils_tip_listener import get_suggestion
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

    multi_call = AutopayMulticalls()
    feed_filter = FundedFeedFilter()

    one_time_tips = OneTimeTips(autopay=autopay)
    funded_feeds = FundedFeeds(autopay=autopay, multi_call=multi_call, feed_filter=feed_filter)

    feed_tips = await funded_feeds.get_feed_tips()
    onetime_tips = await one_time_tips.get_one_time_tip_funded_queries()

    if not feed_tips and not onetime_tips:
        logger.info("No tips available in autopay")
        return None, None

    suggestion = get_suggestion(feed_tips, onetime_tips)
    query_data = suggestion[0]
    tip_amount = suggestion[1]
    qtag = feed_filter.qtag_from_feed_catalog(query_data)
    if qtag:
        if qtag in CATALOG_FEEDS:
            feed: DataFeed[Any] = CATALOG_FEEDS[qtag]  # type: ignore
            return feed, tip_amount
        elif qtag in LEGACY_DATAFEEDS:
            feed: DataFeed[Any] = LEGACY_DATAFEEDS[qtag]  # type: ignore
            return feed, tip_amount

    suggested_qtyp_name = feed_filter.decode_typ_name(query_data)

    try:
        feed = DATAFEED_BUILDER_MAPPING[suggested_qtyp_name]
    except KeyError as e:
        logger.info(f"Query type {e} not supported!")
        return None, None
    query = feed_filter.get_query_from_qtyp_name(query_data, suggested_qtyp_name)
    feed.query = query  # type: ignore

    print(feed, "feed")
    return feed, tip_amount
