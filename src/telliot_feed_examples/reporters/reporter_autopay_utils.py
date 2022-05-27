import math
from dataclasses import dataclass
from typing import Any
from typing import Optional
from typing import Tuple

from eth_abi import decode_single
from telliot_core.data.query_catalog import query_catalog
from telliot_core.tellor.tellorflex.autopay import TellorFlexAutopayContract
from telliot_core.utils.log import get_logger
from telliot_core.utils.response import error_status
from telliot_core.utils.timestamp import TimeStamp

from telliot_feed_examples.feeds import CATALOG_FEEDS


logger = get_logger(__name__)

# Mapping of queryId to query tag for supported queries
CATALOG_QUERY_IDS = {
    query_catalog._entries[tag].query_id: tag for tag in query_catalog._entries
}


@dataclass
class FeedDetails:
    """Data types for feed details contract response"""

    reward: int
    balance: int
    startTime: int
    interval: int
    window: int
    priceThreshold: int
    feedsWithFundingIndex: int


async def get_single_tip(
    query_id: bytes,
    autopay: TellorFlexAutopayContract,
) -> Optional[Any]:
    """Returns a suggested query with a single tip to report.

    Pulls query_ids with tips available from the tellor autopay
    contract, checks if query catalog items have a tip and returns tip amount
    """
    if not autopay.connect().ok:
        msg = "can't suggest single tip for autopay contract not connected"
        error_status(note=msg, log=logger.critical)
        return None

    # gets available tip amount for a query id
    tips, status = await autopay.get_current_tip(query_id=query_id)
    if not status.ok:
        msg = "unable to read getCurrentTip in autopay"
        error_status(note=msg, log=logger.warning)
        return None

    return tips


async def get_feed_tip(
    query_id: str, autopay: TellorFlexAutopayContract
) -> Optional[int]:

    if not autopay.connect().ok:
        msg = "can't suggest feed, autopay contract not connected"
        error_status(note=msg, log=logger.critical)
        return None
    current_time = TimeStamp.now().ts

    # list of feed ids where a query id has tips
    feed_ids, status = await autopay.read("getCurrentFeeds", _queryId=query_id)

    if not status.ok:
        msg = "can't get feed details to calculate tips"
        error_status(note=msg, log=logger.warning)
        return None

    feed_query_dict = {}
    for i in feed_ids:
        # loop over the feed ids and get a tips sum for a query id
        feed_id = f"0x{i.hex()}"
        feed_details, status = await autopay.read("getDataFeed", _feedId=feed_id)
        if not status.ok:
            msg = "couldn't get feed details from contract"
            error_status(note=msg, log=logger.warning)
            continue

        if feed_details is not None:
            try:
                feed_details = FeedDetails(*feed_details)
            except TypeError:
                msg = "couldn't decode feed details from contract"
                error_status(note=msg, log=logger.error)
                continue
        else:
            msg = "No feed details returned from contract"
            error_status(note=msg, log=logger.warning)
            continue

        if feed_details.balance <= 0:
            msg = f"{CATALOG_QUERY_IDS[query_id]}, feed has no remaining balance"
            error_status(note=msg, log=logger.warning)
            continue

        # next two variables are used to check if value to be submitted
        # is first in interval window to be eligible for tip
        # finds closest interval n to timestamp
        n = math.floor((current_time - feed_details.startTime) / feed_details.interval)
        # finds timestamp c of interval n
        c = feed_details.startTime + (feed_details.interval * n)
        response, status = await autopay.read("getCurrentValue", _queryId=query_id)

        if not status.ok:
            msg = "couldn't get value before from getCurrentValue"
            error_status(note=msg, log=logger.warning)
            continue
        # if submission will be first set before values to zero
        if not response[0]:
            value_before_now = 0
            timestamp_before_now = 0
        else:
            value_before_now = decode_single("(uint256)", response[1])[0] / 1e18
            timestamp_before_now = response[2]

        rules = [
            (current_time - c) < feed_details.window,
            timestamp_before_now < c,
        ]

        if not all(rules):
            msg = f"{CATALOG_QUERY_IDS[query_id]}, isn't eligible for a tip"
            error_status(note=msg, log=logger.info)
            continue

        if feed_details.priceThreshold == 0:
            feed_query_dict[i] = feed_details.reward
        else:
            datafeed = CATALOG_FEEDS[CATALOG_QUERY_IDS[query_id]]
            value_now = await datafeed.source.fetch_new_datapoint()
            if not value_now:
                note = f"Unable to fetch {datafeed} price for tip calculation"
                error_status(note=note, log=logger.warning)
                continue
            value_now = value_now[0]

            if value_before_now == 0:
                price_change = 10000

            elif value_now >= value_before_now:
                price_change = (
                    10000 * (value_now - value_before_now)
                ) / value_before_now

            else:
                price_change = (
                    10000 * (value_before_now - value_now)
                ) / value_before_now

            if price_change > feed_details.priceThreshold:
                feed_query_dict[i] = feed_details.reward

    tips_total = sum(feed_query_dict.values())
    if tips_total > 0:
        logger.info(
            f"{CATALOG_QUERY_IDS[query_id]} has potentially {tips_total/1e18} in tips"
        )

    return tips_total


async def autopay_suggested_report(
    autopay: TellorFlexAutopayContract,
) -> Tuple[Optional[str], Any]:
    chain = autopay.node.chain_id

    if chain in (137, 80001):
        assert isinstance(autopay, TellorFlexAutopayContract)

        # helper function to add values when combining dicts with same key
        def add_values(val_1: Optional[int], val_2: Optional[int]) -> Optional[int]:
            if not val_1:
                return val_2
            elif not val_2:
                return val_1
            else:
                return val_1 + val_2

        query_id_lis, status = await autopay.read("getFundedQueryIds")

        # get query_ids with one time tips
        singletip_dict = {
            j: await get_single_tip(bytes.fromhex(i[2:]), autopay)
            for i, j in CATALOG_QUERY_IDS.items()
            if bytes.fromhex(i[2:]) in query_id_lis
        }
        # get query_ids with active feeds
        datafeed_dict = {
            j: await get_feed_tip(i, autopay)
            for i, j in CATALOG_QUERY_IDS.items()
            if "legacy" in j or "spot" in j
        }

        # remove none type
        single_tip_suggestion = {i: j for i, j in singletip_dict.items() if j}
        datafeed_suggestion = {i: j for i, j in datafeed_dict.items() if j}

        # combine feed dicts and add tips for duplicate query ids
        combined_dict = {
            key: add_values(
                single_tip_suggestion.get(key), datafeed_suggestion.get(key)
            )
            for key in single_tip_suggestion | datafeed_suggestion
        }
        # get feed with most tips
        tips_sorted = sorted(
            combined_dict.items(), key=lambda item: item[1], reverse=True  # type: ignore
        )
        if tips_sorted:
            suggested_feed = tips_sorted[0]
            return suggested_feed[0], suggested_feed[1]
        else:
            return None, None
    else:
        return None, None
