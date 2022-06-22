import asyncio
import math
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any
from typing import Dict
from typing import Optional
from typing import Tuple

from eth_abi import decode_single
from multicall import Call
from multicall import Multicall
from multicall import multicall
from multicall.constants import MULTICALL2_ADDRESSES
from multicall.constants import MULTICALL_ADDRESSES
from multicall.constants import Network
from telliot_core.tellor.tellorflex.autopay import TellorFlexAutopayContract
from telliot_core.utils.response import error_status
from telliot_core.utils.timestamp import TimeStamp
from web3.main import Web3

from telliot_feed_examples.feeds import CATALOG_FEEDS
from telliot_feed_examples.queries.query_catalog import query_catalog
from telliot_feed_examples.utils.log import get_logger

logger = get_logger(__name__)

# add testnet support for multicall that aren't avaialable in the package
Network.Mumbai = 80001
MULTICALL_ADDRESSES[Network.Mumbai] = MULTICALL2_ADDRESSES[
    Network.Mumbai
] = "0x35583BDef43126cdE71FD273F5ebeffd3a92742A"
Network.ArbitrumRinkeby = 421611
MULTICALL_ADDRESSES[Network.ArbitrumRinkeby] = MULTICALL2_ADDRESSES[
    Network.ArbitrumRinkeby
] = "0xf609687230a65E8bd14caceDEfCF2dea9c15b242"


async def run_in_subprocess(coro: Any, *args: Any, **kwargs: Any) -> Any:
    return await asyncio.get_event_loop().run_in_executor(ThreadPoolExecutor(16), coro, *args, **kwargs)


multicall.run_in_subprocess = run_in_subprocess

# Mapping of queryId to query tag for supported queries
CATALOG_QUERY_IDS = {query_catalog._entries[tag].query.query_id: tag for tag in query_catalog._entries}


@dataclass
class Tag:
    query_tag: str
    feed_id: str


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


class AutopayCalls:
    def __init__(self, autopay: TellorFlexAutopayContract, catalog: Dict[bytes, str] = CATALOG_QUERY_IDS):
        self.autopay = autopay
        self.w3: Web3 = autopay.node._web3
        self.catalog = catalog

    async def get_current_feeds(self, require_success: bool = True) -> Any:
        calls = [
            Call(
                self.autopay.address,
                ["getCurrentFeeds(bytes32)(bytes32[])", query_id],
                [[self.catalog[query_id], None]],
            )
            for query_id, tag in self.catalog.items()
            if "legacy" in tag or "spot" in tag
        ]
        multi_call = Multicall(calls=calls, _w3=self.w3, require_success=require_success)
        data = await multi_call.coroutine()
        return data

    async def get_feed_details(self, require_success: bool = True) -> Any:
        """Returns dictionary of autopay response from getCurrentValues and getDataFeed function call at once"""
        current_feeds = await self.get_current_feeds()
        get_data_feed_call = [
            Call(
                self.autopay.address,
                ["getDataFeed(bytes32)((uint256,uint256,uint256,uint256,uint256,uint256,uint256))", query_id],
                [[("current_feeds", tag, query_id.hex()), None]],
            )
            for tag, ids in current_feeds.items()
            for query_id in ids
        ]
        get_current_values_call = [
            Call(
                self.autopay.address,
                ["getCurrentValue(bytes32)(bool,bytes,uint256)", query_id],
                [
                    [("current_values", self.catalog[query_id]), None],
                    [("current_values", self.catalog[query_id], "current_price"), self._current_price],
                    [("current_values", self.catalog[query_id], "timestamp"), None],
                ],
            )
            for query_id, tag in self.catalog.items()
            if "legacy" in tag or "spot" in tag
        ]
        calls = get_data_feed_call + get_current_values_call
        multi_call = Multicall(calls=calls, _w3=self.w3, require_success=require_success)
        feed_details = await multi_call.coroutine()
        return feed_details

    async def get_current_tip(self, require_success: bool = False) -> Any:
        """
        Returns response from autopay getCurrenTip call
        require_success is False because autopay returns an
        error if tip amount is zero
        """
        calls = [
            Call(self.autopay.address, ["getCurrentTip(bytes32)(uint256)", query_id], [[self.catalog[query_id], None]])
            for query_id in self.catalog
        ]
        multi_call = Multicall(calls=calls, _w3=self.w3, require_success=require_success)
        data = await multi_call.coroutine()
        return data

    # Helper to decode price value from oracle
    def _current_price(self, *val: Any) -> Any:
        if len(val) > 1:
            if val[1] == b"":
                return val[1]
            return Web3.toInt(hexstr=val[1].hex()) / 1e18
        return Web3.toInt(hexstr=val[0].hex()) / 1e18 if val[0] != b"" else val[0]


async def get_feed_tip(query_id: bytes, autopay: TellorFlexAutopayContract) -> Optional[int]:

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
    for feed_id_bytes in feed_ids:
        # loop over the feed ids and get a tips sum for a query id
        feed_id = f"0x{feed_id_bytes.hex()}"
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
            except Exception as e:
                msg = f"unknown error decoding feed details from contract: {e}"
                error_status(note=msg, log=logger.error)
                continue
        else:
            msg = "No feed details returned from contract"
            error_status(note=msg, log=logger.warning)
            continue

        if feed_details.balance <= 0:
            msg = f"{CATALOG_QUERY_IDS[query_id]}, autopay feed has no remaining balance"
            error_status(note=msg, log=logger.warning)
            continue

        # Check if value to be submitted will be first in interval window to
        # be eligible for tip

        # Number of intervals since start time
        num_intervals = math.floor((current_time - feed_details.startTime) / feed_details.interval)
        # Start time of latest submission window
        current_window_start = feed_details.startTime + (feed_details.interval * num_intervals)

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
            (current_time - current_window_start) < feed_details.window,
            timestamp_before_now < current_window_start,
        ]

        if not all(rules):
            msg = f"{CATALOG_QUERY_IDS[query_id]}, isn't eligible for a tip"
            error_status(note=msg, log=logger.info)
            continue

        if feed_details.priceThreshold == 0:
            feed_query_dict[feed_id_bytes] = feed_details.reward
        else:
            datafeed = CATALOG_FEEDS[CATALOG_QUERY_IDS[query_id]]
            value_now = await datafeed.source.fetch_new_datapoint()  # type: ignore
            if not value_now:
                note = f"Unable to fetch {datafeed} price for tip calculation"
                error_status(note=note, log=logger.warning)
                continue
            value_now = value_now[0]

            if value_before_now == 0:
                price_change = 10000

            elif value_now >= value_before_now:
                price_change = (10000 * (value_now - value_before_now)) / value_before_now

            else:
                price_change = (10000 * (value_before_now - value_now)) / value_before_now

            if price_change > feed_details.priceThreshold:
                feed_query_dict[feed_id_bytes] = feed_details.reward

    tips_total = sum(feed_query_dict.values())
    if tips_total > 0:
        logger.info(f"{CATALOG_QUERY_IDS[query_id]} has potentially {tips_total/1e18} in tips")

    return tips_total


async def get_one_time_tips(
    autopay: TellorFlexAutopayContract,
) -> Any:
    one_time_tips = AutopayCalls(autopay=autopay, catalog=CATALOG_QUERY_IDS)
    return await one_time_tips.get_current_tip()


async def get_continuous_tips(
    autopay: TellorFlexAutopayContract,
) -> Any:
    tipping_feeds = AutopayCalls(autopay=autopay, catalog=CATALOG_QUERY_IDS)
    feed_details = await tipping_feeds.get_feed_details()
    current_feeds = {(key[1], key[2]): value for key, value in feed_details.items() if key[0] == "current_feeds"}
    current_values = {}
    for key, value in feed_details.items():
        if key[0] == "current_values" and len(key) > 2:
            current_values[(key[1], key[2])] = value
        else:
            current_values[key[1]] = value
    return await _get_feed_suggestion(current_feeds, current_values)


async def autopay_suggested_report(
    autopay: TellorFlexAutopayContract,
) -> Tuple[Optional[str], Any]:
    chain = autopay.node.chain_id
    if chain in (137, 80001, 69, 1666600000, 1666700000, 421611):
        assert isinstance(autopay, TellorFlexAutopayContract)
        # get query_ids with one time tips
        singletip_dict = await get_one_time_tips(autopay)
        # get query_ids with active feeds
        datafeed_dict = await get_continuous_tips(autopay)

        # remove none type
        single_tip_suggestion = {i: j for i, j in singletip_dict.items() if j}
        datafeed_suggestion = {i: j for i, j in datafeed_dict.items() if j}

        # combine feed dicts and add tips for duplicate query ids
        combined_dict = {
            key: _add_values(single_tip_suggestion.get(key), datafeed_suggestion.get(key))
            for key in single_tip_suggestion | datafeed_suggestion
        }
        # get feed with most tips
        tips_sorted = sorted(combined_dict.items(), key=lambda item: item[1], reverse=True)  # type: ignore
        if tips_sorted:
            suggested_feed = tips_sorted[0]
            return suggested_feed[0], suggested_feed[1]
        else:
            return None, None
    else:
        return None, None


async def _get_feed_suggestion(feeds: Any, current_values: Any) -> Any:

    current_time = TimeStamp.now().ts
    query_id_with_tips = {}

    for query_tag, feed_id in feeds:  # i is (query_id,feed_id)
        if feeds[(query_tag, feed_id)] is not None:  # feed_detail[i] is (details)
            try:
                feed_details = FeedDetails(*feeds[(query_tag, feed_id)])
            except TypeError:
                msg = "couldn't decode feed details from contract"
                continue
            except Exception as e:
                msg = f"unknown error decoding feed details from contract: {e}"
                continue

        if feed_details.balance <= 0:
            continue
        num_intervals = math.floor((current_time - feed_details.startTime) / feed_details.interval)
        # Start time of latest submission window
        current_window_start = feed_details.startTime + (feed_details.interval * num_intervals)

        if not current_values[query_tag]:
            value_before_now = 0
            timestamp_before_now = 0
        else:
            value_before_now = current_values[(query_tag, "current_price")]
            timestamp_before_now = current_values[(query_tag, "timestamp")]

        rules = [
            (current_time - current_window_start) < feed_details.window,
            timestamp_before_now < current_window_start,
        ]
        if not all(rules):
            msg = f"{query_tag}, isn't eligible for a tip"
            error_status(note=msg, log=logger.info)
            continue

        if feed_details.priceThreshold == 0:
            if query_tag not in query_id_with_tips:
                query_id_with_tips[query_tag] = feed_details.reward
            else:
                query_id_with_tips[query_tag] += feed_details.reward
        else:
            datafeed = CATALOG_FEEDS[query_tag]
            value_now = await datafeed.source.fetch_new_datapoint()  # type: ignore
            if not value_now:
                note = f"Unable to fetch {datafeed} price for tip calculation"
                error_status(note=note, log=logger.warning)
                continue
            value_now = value_now[0]

            if value_before_now == 0:
                price_change = 10000

            elif value_now >= value_before_now:
                price_change = (10000 * (value_now - value_before_now)) / value_before_now

            else:
                price_change = (10000 * (value_before_now - value_now)) / value_before_now

            if price_change > feed_details.priceThreshold:
                if query_tag not in query_id_with_tips:
                    query_id_with_tips[query_tag] = feed_details.reward
                else:
                    query_id_with_tips[query_tag] += feed_details.reward

    return query_id_with_tips


def _add_values(x: Optional[int], y: Optional[int]) -> Optional[int]:
    """Helper function to add values when combining dicts with same key"""
    return sum((num for num in (x, y) if num is not None))
