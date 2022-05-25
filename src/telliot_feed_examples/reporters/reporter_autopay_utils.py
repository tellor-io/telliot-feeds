import math
from typing import Any
from typing import Optional
from typing import Tuple

from eth_abi import decode_single
from telliot_core.data.query_catalog import query_catalog
from telliot_core.tellor.tellorflex.autopay import TellorFlexAutopayContract
from telliot_core.utils.log import get_logger
from telliot_core.utils.response import error_status
from telliot_core.utils.timestamp import TimeStamp
from web3.providers.rpc import HTTPProvider

from telliot_feed_examples.feeds import CATALOG_FEEDS
from telliot_feed_examples.reporters.tip_listener.event_scanner import EventScanner
from telliot_feed_examples.reporters.tip_listener.json_state import JSONifiedState


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


async def get_single_tip(
    query_id: bytes,
    autopay: TellorFlexAutopayContract,
) -> Optional[int]:
    """Returns a suggested query with a single tip to report.

    Pulls query_ids with tips available from the tellor autopay
    contract, checks if query catalog items have a tip and returns tip amount
    """
    if not autopay.connect().ok:
        msg = "can't suggest single tip for autopay contract not connected"
        error_status(note=msg, log=logger.critical)
        return None

    current_time = TimeStamp.now().ts
    tips, status = await autopay.read("getPastTips", _queryId=query_id)
    if not status.ok:
        msg = "unable to read getPastTipCount in autopay"
        error_status(note=msg, log=logger.warning)
        return None
    count = len(tips)
    if count > 0:
        mini = 0
        maxi = count
        while maxi - mini > 1:
            mid = int((maxi + mini) / 2)
            tip_info = tips[mid]
            if tip_info[1] > current_time:
                maxi = mid
            else:
                mini = mid

        timestamp_before, status = await autopay.read(
            "getCurrentValue", _queryId=query_id
        )
        if not status.ok:
            msg = "unable to read current value"
            error_status(note=msg, log=logger.warning)
            return None
        tip_info = tips[mini]
        if timestamp_before[2] < tip_info[1]:
            logger.info(
                msg=f"{query_ids_in_catalog['0x'+query_id.hex()]}\
                        has {tip_info[0]/1e18} in potential tips"
            )
            return int(tip_info[0])

    return None


async def get_feed_tip(
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
                msg = f"{query_ids_in_catalog[query_id]}, feed has no remaining balance"
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
        # if submission will be first set before values to zero
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
            if not value_now:
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

        # Remove the default JSON-RPC retry middleware
        # as it correctly cannot handle eth_getLogs block range
        # throttle down.
        HTTPProvider(autopay.node.url).middlewares.clear()  # type: ignore

        state = JSONifiedState()
        state.restore()

        scanner = EventScanner(
            web3=autopay.node.web3,
            state=state,
            contract=autopay.contract,
            events=[
                autopay.contract.events.DataFeedFunded,
                autopay.contract.events.TipAdded,
            ],
            filters={"address": autopay.address},
            # Infura max block range
            max_chunk_scan_size=3499,
        )

        # Assume we might have scanned the blocks all the way to the last Ethereum block
        # that mined a few seconds before the previous scan run ended.
        # Because there might have been a minor Etherueum chain reorganisations
        # since the last scan ended, we need to discard
        # the last few blocks from the previous scan results.
        chain_reorg_safety_blocks = 10
        scanner.delete_potentially_forked_block_data(
            state.get_last_scanned_block() - chain_reorg_safety_blocks
        )

        # Scan from [last block scanned] - [latest ethereum block]
        # Note that our chain reorg safety blocks cannot go negative
        start_block = max(state.get_last_scanned_block() - chain_reorg_safety_blocks, 0)
        end_block = scanner.get_suggested_scan_end_block()

        # Run the scan
        scanner.scan(start_block, end_block)

        if state.one_time_tips_count() > 10:
            # get query_ids with one time tips
            query_id_lis, status = await autopay.read("getFundedQueryIds")
            if status.ok:
                msg = "unable to read getFundedQueryIds from autopay"
                error_status(note=msg, log=logger.warning)
                singletip_dict = {}
            singletip_dict = {
                j: await get_single_tip(bytes.fromhex(i[2:]), autopay)
                for i, j in query_ids_in_catalog.items()
                if bytes.fromhex(i[2:]) in query_id_lis
            }
            single_tip_suggestion = {i: j for i, j in singletip_dict.items() if j}

            if single_tip_suggestion:
                state.decrement_one_time_tip()
            else:
                state.reset_one_time_tip_count()
        else:
            single_tip_suggestion = {}

        if state.continuous_feed_count() > 0:
            # get query_ids with active feeds
            datafeed_dict = {
                j: await get_feed_tip(i, autopay)
                for i, j in query_ids_in_catalog.items()
                if "legacy" in j or "spot" in j
            }

            datafeed_suggestion = {i: j for i, j in datafeed_dict.items() if j}

            if datafeed_suggestion:
                state.decrement_continuous_feed()
            else:
                state.reset_continuous_feed_count()

        else:
            datafeed_suggestion = {}

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
