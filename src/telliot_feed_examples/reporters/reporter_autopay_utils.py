import math
from typing import Optional
from typing import Tuple

from eth_abi import decode_single
from telliot_core.data.query_catalog import query_catalog
from telliot_core.tellor.tellorflex.autopay import TellorFlexAutopayContract
from telliot_core.utils.response import error_status
from telliot_core.utils.timestamp import TimeStamp

from telliot_feed_examples.feeds import CATALOG_FEEDS
from telliot_feed_examples.utils.log import get_logger


logger = get_logger(__name__)

# List of currently active queries
query_ids_in_catalog = {
    query_catalog._entries[tag].query_id: tag for tag in query_catalog._entries
}


# Mapping to feed details
class DetailsMap:
    reward = 0
    balance = 1
    startTime = 2
    interval = 3
    window = 4
    priceThreshold = 5
    feedsWithFundingIndex = 6


detail = DetailsMap()


async def single_tip_suggested_query_id(
    autopay: TellorFlexAutopayContract,
) -> Tuple[Optional[str], Optional[int]]:
    """Returns the currently suggested query to for a single tip report against.

    Pulls query_ids with tips available from the tellor autopay
    contract, checks if query ids exist in the query catalog,
    then sorts them from highest tip amount to lowest
    """
    if not autopay.connect().ok:
        msg = "can't suggest single tip query id, autopay contract not connected"
        error_status(note=msg, log=logger.critical)
        return None, None
    query_id_lis, status = await autopay.read("getFundedQueryIds")
    tips_dictionary = {}
    current_time = TimeStamp.now().ts
    for i in query_id_lis:
        query_id = f"0x{i.hex()}"
        if query_id in query_ids_in_catalog:
            length = await autopay.read("getPastTipCount", _queryId=i)
            count = length[0]
            if count > 0:
                mini = 0
                maxi = count
                while maxi - mini > 1:
                    mid = int((maxi + mini) / 2)
                    tip_info, status = await autopay.read("tips", query_id, mid)
                    if tip_info[1] > current_time:
                        maxi = mid
                    else:
                        mini = mid

                timestamp_before, status = await autopay.read(
                    "getCurrentValue", _queryId=i
                )
                tip_info, status = await autopay.read("tips", i, mini)
                if timestamp_before[2] < tip_info[1]:
                    tips_dictionary[i] = tip_info[0] / 1e18
                else:
                    continue

    if status.ok:
        tips_sorted = sorted(
            tips_dictionary.items(),
            key=lambda item: item[1],  # type: ignore
            reverse=True,
        )
        if tips_sorted:
            suggested_qtag = f"0x{tips_sorted[0][0].hex()}"
            suggested_qtag_tip = int(tips_sorted[0][1])
            return query_ids_in_catalog[suggested_qtag], int(suggested_qtag_tip * 1e18)
        else:
            return None, None
    else:
        msg = "can't get FundedQueryIds"
        error_status(note=msg, log=logger.warning)
        return None, None


async def get_feed_details(
    query_id: str, autopay: TellorFlexAutopayContract
) -> Optional[int]:

    if not autopay.connect().ok:
        msg = "can't suggest feed, autopay contract not connected"
        error_status(note=msg, log=logger.critical)
        return None
    current_time = TimeStamp.now().ts
    feed_ids, status = await autopay.read("getCurrentFeeds", _queryId=query_id)

    if not status.ok:
        msg = "can't get feed details to calculate tips"
        error_status(note=msg, log=logger.warning)
        return None

    feed_query_dict = {}
    for i in feed_ids:
        if i:
            feed_id = f"0x{i.hex()}"
            feed_details, status = await autopay.read("getDataFeed", _feedId=feed_id)

            if not status.ok:
                msg = "couldn't get feed details from contract"
                error_status(note=msg, log=logger.warning)
                return None

            if (
                feed_details[detail.balance] <= 0 and feed_details[detail.reward] <= 0
            ) or feed_details[detail.balance] < feed_details[detail.reward]:
                msg = f"{feed_id}, feed has no remaining balance"
                error_status(note=msg, log=logger.warning)
                return None

        # next two variables are used to check if value to be submitted
        # is first in interval window to be eligible for tip
        # finds closest interval n to timestamp
        n = math.floor(
            (current_time - feed_details[detail.startTime])
            / feed_details[detail.interval]
        )
        # finds timestamp c of interval n
        c = feed_details[detail.startTime] + (feed_details[detail.interval] * n)
        response, status = await autopay.read("getCurrentValue", _queryId=query_id)

        if not status.ok:
            msg = "couldn't get value before from getCurrentValue"
            error_status(note=msg, log=logger.warning)
            return None

        if not response[0]:
            value_before_now = 0
            timestamp_before_now = 0
        else:
            value_before_now = decode_single("(uint256)", response[1])[0] / 1e18
            timestamp_before_now = response[2]

        rules = [
            (current_time - c) < feed_details[detail.window],
            timestamp_before_now < c,
        ]

        if not all(rules):
            msg = f"{query_ids_in_catalog[query_id]}, isn't eligible for a tip"
            error_status(note=msg, log=logger.info)
            return None

        if feed_details[detail.priceThreshold] == 0:
            feed_query_dict[i] = feed_details[detail.reward]
        else:
            datafeed = CATALOG_FEEDS[query_ids_in_catalog[query_id]]
            value_now = await datafeed.source.fetch_new_datapoint()
            if value_now is None:
                note = f"Unable to fetch {datafeed} price for tip calculation"
                error_status(note=note, log=logger.warning)
                return None
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

            if price_change > feed_details[detail.priceThreshold]:
                feed_query_dict[i] = feed_details[detail.reward]

    tips_total = sum(feed_query_dict.values())
    if tips_total > 0:
        logger.info(
            f"{query_ids_in_catalog[query_id]} has potentially {tips_total/1e18} in tips"
        )

    return tips_total


async def autopay_suggested_report(
    autopay: TellorFlexAutopayContract,
) -> Tuple[Optional[str], Optional[int]]:
    chain = autopay.node.chain_id

    if chain in (137, 80001):
        assert isinstance(autopay, TellorFlexAutopayContract)
        datafeed_dict = {
            j: await get_feed_details(i, autopay)
            for i, j in query_ids_in_catalog.items()
            if "legacy" in j or "spot" in j
        }
        datafeed_suggestion = {i: j for i, j in datafeed_dict.items() if j}
        datafeed_tips_sorted = sorted(
            datafeed_suggestion.items(), key=lambda item: item[1], reverse=True
        )
        (
            single_suggested_qtag,
            single_suggested_tip,
        ) = await single_tip_suggested_query_id(autopay=autopay)
        # checks if there is a suggested multitip feed
        # to compare with suggested single tip
        if datafeed_tips_sorted:
            multitip_suggested_qtag, multitip_suggested_tip = datafeed_tips_sorted[0]
        else:
            return single_suggested_qtag, single_suggested_tip
        # checks if there is a suggested single tip feed to compare with multitip feed
        if not single_suggested_qtag:
            return multitip_suggested_qtag, multitip_suggested_tip

        # checks if suggested multtip and single tip are the same and adds tip
        if multitip_suggested_qtag == single_suggested_qtag:
            return multitip_suggested_qtag, (
                multitip_suggested_tip + single_suggested_tip  # type: ignore
            )
        # checks if suggested multitip feed is greater than suggested single tip feed
        elif multitip_suggested_tip > single_suggested_tip:  # type: ignore
            return multitip_suggested_qtag, multitip_suggested_tip
        else:
            return single_suggested_qtag, single_suggested_tip

    else:
        return None, None
