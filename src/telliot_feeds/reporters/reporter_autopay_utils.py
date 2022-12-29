"""
Uses Python's interface from https://github.com/banteg/multicall.py.git for MakerDAO's multicall contract.
Multicall contract helps reduce node calls by combining contract function calls
and returning the values all together. This is helpful especially if API nodes like Infura are being used.
"""
import math
from dataclasses import dataclass
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

from clamfig.base import Registry
from eth_abi import decode_single
from multicall import Call
from multicall import Multicall
from telliot_core.tellor.tellorflex.autopay import TellorFlexAutopayContract
from telliot_core.utils.response import error_status
from telliot_core.utils.timestamp import TimeStamp
from web3.exceptions import ContractLogicError
from web3.main import Web3

from telliot_feeds.feeds import CATALOG_FEEDS
from telliot_feeds.queries.query_catalog import query_catalog
from telliot_feeds.reporters.tips import CATALOG_QUERY_IDS
from telliot_feeds.utils.log import get_logger

logger = get_logger(__name__)


# chains where autopay contract is deployed
AUTOPAY_CHAINS = (137, 80001, 69, 1666600000, 1666700000, 421611, 42161, 10200)


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

    async def get_current_feeds(self, require_success: bool = False) -> Optional[Dict[str, Any]]:
        """
        Getter for:
        - feed ids list for each query id in catalog
        - a report's timestamp index from oracle for current timestamp and three months ago
        (used for getting all timestamps for the past three months)

        Reason of why three months: reporters can't claim tips from funded feeds past three months
        getting three months of timestamp is useful to determine if there will be a balance after every eligible
        timestamp claims a tip thus draining the feeds balance as a result

        Return:
        - {'tag': (feed_id_bytes,), ('tag', 'current_time'): index_at_timestamp,
        ('tag', 'three_mos_ago'): index_at_timestamp}
        """
        calls = []
        current_time = TimeStamp.now().ts
        three_mos_ago = current_time - 7889238  # 3 months in seconds
        for query_id, tag in self.catalog.items():
            if "legacy" in tag or "spot" in tag:
                calls.append(
                    Call(
                        self.autopay.address,
                        ["getCurrentFeeds(bytes32)(bytes32[])", query_id],
                        [[tag, None]],
                    )
                )
                calls.append(
                    Call(
                        self.autopay.address,
                        ["getIndexForDataBefore(bytes32,uint256)(bool,uint256)", query_id, current_time],
                        [["disregard_boolean", None], [(tag, "current_time"), None]],
                    )
                )
                calls.append(
                    Call(
                        self.autopay.address,
                        ["getIndexForDataBefore(bytes32,uint256)(bool,uint256)", query_id, three_mos_ago],
                        [["disregard_boolean", None], [(tag, "three_mos_ago"), None]],
                    )
                )
        data = await safe_multicall(calls, self.w3, require_success)
        if not data:
            return None
        try:
            data.pop("disregard_boolean")
        except KeyError as e:
            msg = f"No feeds returned by multicall, KeyError: {e}"
            logger.warning(msg)
        return data

    async def get_feed_details(self, require_success: bool = False) -> Any:
        """
        Getter for:
        - timestamps for three months of reports to oracle using queryId and index
        - feed details of all feedIds for every queryId
        - current values from oracle for every queryId in catalog (used to determine
        can submit now in eligible window)

        Return:
        - {('current_feeds', 'tag', 'feed_id'): [feed_details], ('current_values', 'tag'): True,
        ('current_values', 'tag', 'current_price'): float(price),
        ('current_values', 'tag', 'timestamp'): 1655137179}
        """

        current_feeds = await self.get_current_feeds()

        if not current_feeds:
            logger.info("No available feeds")
            return None

        # separate items from current feeds
        # multicall for multiple different functions returns different types of data at once
        # ie the response is {"tag": (feedids, ), ('trb-usd-spot', 'current_time'): 0,
        # ('trb-usd-spot', 'three_mos_ago'): 0,eth-jpy-spot: (),'eth-jpy-spot', 'current_time'): 0,
        # ('eth-jpy-spot', 'three_mos_ago'): 0}
        # here we filter out the tag key if it is string and its value is of length > 0

        tags_with_feed_ids = {
            tag: feed_id
            for tag, feed_id in current_feeds.items()
            if (not isinstance(tag, tuple) and (current_feeds[tag]))
        }
        idx_current: List[int] = []  # indices for every query id reports' current timestamps
        idx_three_mos_ago: List[int] = []  # indices for every query id reports' three months ago timestamps
        tags: List[str] = []  # query tags from catalog
        for key in current_feeds:
            if isinstance(key, tuple) and key[0] in tags_with_feed_ids:
                if key[1] == "current_time":
                    idx_current.append(current_feeds[key])
                    tags.append((key[0], tags_with_feed_ids[key[0]]))
                else:
                    idx_three_mos_ago.append(current_feeds[key])

        merged_indices = list(zip(idx_current, idx_three_mos_ago))
        merged_query_idx = dict(zip(tags, merged_indices))

        get_timestampby_query_id_n_idx_call = []

        tag: str
        for (tag, _), (end, start) in merged_query_idx.items():
            if start and end:
                for idx in range(start, end):

                    get_timestampby_query_id_n_idx_call.append(
                        Call(
                            self.autopay.address,
                            [
                                "getTimestampbyQueryIdandIndex(bytes32,uint256)(uint256)",
                                query_catalog._entries[tag].query.query_id,
                                idx,
                            ],
                            [[(tag, idx), None]],
                        )
                    )

        def _to_list(_: bool, val: Any) -> List[Any]:
            """Helper function, converts feed_details from tuple to list"""
            return list(val)

        get_data_feed_call = []

        feed_ids: List[bytes]
        for tag, feed_ids in merged_query_idx:
            for feed_id in feed_ids:
                c = Call(
                    self.autopay.address,
                    ["getDataFeed(bytes32)((uint256,uint256,uint256,uint256,uint256,uint256,uint256))", feed_id],
                    [[("current_feeds", tag, feed_id.hex()), _to_list]],
                )

                get_data_feed_call.append(c)

        get_current_values_call = []

        for tag, _ in merged_query_idx:

            c = Call(
                self.autopay.address,
                ["getCurrentValue(bytes32)(bool,bytes,uint256)", query_catalog._entries[tag].query.query_id],
                [
                    [("current_values", tag), None],
                    [("current_values", tag, "current_price"), None],
                    [("current_values", tag, "timestamp"), None],
                ],
            )

            get_current_values_call.append(c)

        calls = get_data_feed_call + get_current_values_call + get_timestampby_query_id_n_idx_call
        return await safe_multicall(calls, self.w3, require_success)

    async def reward_claim_status(
        self, require_success: bool = False
    ) -> Tuple[Optional[Dict[Any, Any]], Optional[Dict[Any, Any]], Optional[Dict[Any, Any]]]:
        """
        Getter that checks if a timestamp's tip has been claimed
        """
        feed_details_before_check = await self.get_feed_details()
        if not feed_details_before_check:
            logger.info("No feeds balance to check")
            return None, None, None
        # create a key to use for the first timestamp since it doesn't have a before value that needs to be checked
        feed_details_before_check[(0, 0)] = 0
        timestamp_before_key = (0, 0)

        feeds = {}
        current_values = {}
        for i, j in feed_details_before_check.items():
            if "current_feeds" in i:
                feeds[i] = j
            elif "current_values" in i:
                current_values[i] = j

        reward_claimed_status_call = []
        for _, tag, feed_id in feeds:
            details = FeedDetails(*feeds[(_, tag, feed_id)])
            for keys in list(feed_details_before_check):
                if "current_feeds" not in keys and "current_values" not in keys:
                    if tag in keys:
                        is_first = _is_timestamp_first_in_window(
                            feed_details_before_check[timestamp_before_key],
                            feed_details_before_check[keys],
                            details.startTime,
                            details.window,
                            details.interval,
                        )
                        timestamp_before_key = keys
                        if is_first:
                            reward_claimed_status_call.append(
                                Call(
                                    self.autopay.address,
                                    [
                                        "getRewardClaimedStatus(bytes32,bytes32,uint256)(bool)",
                                        bytes.fromhex(feed_id),
                                        query_catalog._entries[tag].query.query_id,
                                        feed_details_before_check[keys],
                                    ],
                                    [[(tag, feed_id, feed_details_before_check[keys]), None]],
                                )
                            )

        data = await safe_multicall(reward_claimed_status_call, self.w3, require_success)
        if data is not None:
            return feeds, current_values, data
        else:
            return None, None, None

    async def get_current_tip(self, require_success: bool = False) -> Optional[Dict[str, Any]]:
        """
        Return response from autopay getCurrenTip call.
        Default value for require_success is False because AutoPay returns an
        error if tip amount is zero.
        """
        calls = [
            Call(self.autopay.address, ["getCurrentTip(bytes32)(uint256)", query_id], [[self.catalog[query_id], None]])
            for query_id in self.catalog
        ]
        return await safe_multicall(calls, self.w3, require_success)


async def get_feed_tip(query: bytes, autopay: TellorFlexAutopayContract) -> Optional[int]:
    """
    Get total tips for a query id with funded feeds

    - query: if the query exists in the telliot queries catalog then input should be the query id,
    otherwise input should be the query data for newly generated ids in order to determine if submission
    for the query is supported by telliot
    """
    if not autopay.connect().ok:
        msg = "can't suggest feed, autopay contract not connected"
        error_status(note=msg, log=logger.critical)
        return None

    if query in CATALOG_QUERY_IDS:
        query_id = query
        single_query = {query_id: CATALOG_QUERY_IDS[query_id]}
    else:
        try:
            query_data = query
            qtype_name, _ = decode_single("(string,bytes)", query_data)
        except OverflowError:
            logger.warning("Query data not available to decode")
            return None
        if qtype_name not in Registry.registry:
            logger.warning(f"Unsupported query type: {qtype_name}")
            return None
        else:
            query_id = Web3.keccak(query_data)
            CATALOG_QUERY_IDS[query_id] = query_id.hex()
            single_query = {query_id: CATALOG_QUERY_IDS[query_id]}

    autopay_calls = AutopayCalls(autopay, catalog=single_query)
    feed_tips = await get_continuous_tips(autopay, autopay_calls)
    if feed_tips is None:
        tips = 0
        msg = "No feeds available for query id"
        logger.warning(msg)
        return tips
    try:
        tips = feed_tips[CATALOG_QUERY_IDS[query_id]]
    except KeyError:
        msg = f"Tips for {CATALOG_QUERY_IDS[query_id]} not showing"
        logger.warning(CATALOG_QUERY_IDS[query_id])
        return None
    return tips


async def get_one_time_tips(
    autopay: TellorFlexAutopayContract,
) -> Any:
    """
    Check query ids in catalog for one-time-tips and return query id with the most tips
    """
    one_time_tips = AutopayCalls(autopay=autopay, catalog=CATALOG_QUERY_IDS)
    return await one_time_tips.get_current_tip()


async def get_continuous_tips(autopay: TellorFlexAutopayContract, tipping_feeds: Any = None) -> Any:
    """
    Check query ids in catalog for funded feeds, combine tips, and return query id with most tips
    """
    if tipping_feeds is None:
        tipping_feeds = AutopayCalls(autopay=autopay, catalog=CATALOG_QUERY_IDS)
    response = await tipping_feeds.reward_claim_status()
    if response == (None, None, None):
        logger.info("No feeds to check")
        return None
    current_feeds, current_values, claim_status = response
    # filter out feeds that don't have a remaining balance after accounting for claimed tips
    current_feeds = _remaining_feed_balance(current_feeds, claim_status)
    # remove "current_feeds" word from tuple key in current_feeds dict to help when checking
    # current_values dict for corresponding current values
    current_feeds = {(key[1], key[2]): value for key, value in current_feeds.items()}
    values_filtered = {}
    for key, value in current_values.items():
        if len(key) > 2:
            values_filtered[(key[1], key[2])] = value
        else:
            values_filtered[key[1]] = value
    return await _get_feed_suggestion(current_feeds, values_filtered)


async def autopay_suggested_report(
    autopay: TellorFlexAutopayContract,
) -> Tuple[Optional[str], Any]:
    """
    Gets one-time tips and continuous tips then extracts query id with the most tips for a report suggestion

    Return: query id, tip amount
    """
    chain = autopay.node.chain_id
    if chain in AUTOPAY_CHAINS:

        # get query_ids with one time tips
        singletip_dict = await get_one_time_tips(autopay)
        # get query_ids with active feeds
        datafeed_dict = await get_continuous_tips(autopay)

        # remove none type from dict
        single_tip_suggestion = {}
        if singletip_dict is not None:
            single_tip_suggestion = {i: j for i, j in singletip_dict.items() if j}

        datafeed_suggestion = {}
        if datafeed_dict is not None:
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
        logger.warning(f"Chain {chain} does not have Autopay contract support")
        return None, None


async def _get_feed_suggestion(feeds: Any, current_values: Any) -> Any:
    """
    Calculates tips and checks if a submission is in an eligible window for a feed submission
    for a given query_id and feed_ids

    Return: a dict tag:tip amount
    """
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
            # value is always a number for a price oracle submission
            # convert bytes value to int
            try:
                value_before_now = int(int(current_values[(query_tag, "current_price")].hex(), 16) / 1e18)
            except ValueError:
                logger.info("Can't check price threshold, oracle price submission not a number")
                continue
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


async def safe_multicall(calls: List[Call], endpoint: Web3, require_success: bool) -> Optional[Dict[str, Any]]:
    """
    Multicall...call with error handling

    Args:
        calls: list of Call objects, representing calls made by request
        endpoint: web3 RPC endpoint connection
        require_success: throws error if True and contract logic reverts

    Returns:
        data if multicall is successful
    """
    mc = Multicall(calls=calls, _w3=endpoint, require_success=require_success)

    try:
        data: Dict[str, Any] = await mc.coroutine()
        return data
    except ContractLogicError as e:
        msg = f"Contract reversion in multicall request, ContractLogicError: {e}"
        logger.warning(msg)
        return None
    except ValueError as e:
        if "unsupported block number" in str(e):
            msg = f"Unsupported block number in multicall request, ValueError: {e}"
            logger.warning(msg)
            return None
        else:
            msg = f"Error in multicall request, ValueError: {e}"
            return None


def _add_values(x: Optional[int], y: Optional[int]) -> Optional[int]:
    """Helper function to add values when combining dicts with same key"""
    return sum((num for num in (x, y) if num is not None))


def _is_timestamp_first_in_window(
    timestamp_before: int, timestamp_to_check: int, feed_start_timestamp: int, feed_window: int, feed_interval: int
) -> bool:
    """
    Calculates to check if timestamp(timestamp_to_check) is first in window

    Return: bool
    """
    # Number of intervals since start time
    num_intervals = math.floor((timestamp_to_check - feed_start_timestamp) / feed_interval)
    # Start time of latest submission window
    current_window_start = feed_start_timestamp + (feed_interval * num_intervals)
    eligible = [(timestamp_to_check - current_window_start) < feed_window, timestamp_before < current_window_start]
    return all(eligible)


def _remaining_feed_balance(current_feeds: Any, reward_claimed_status: Any) -> Any:
    """
    Checks if a feed has a remaining balance

    """
    for _, tag, feed_id in current_feeds:
        details = FeedDetails(*current_feeds[_, tag, feed_id])
        balance = details.balance
        if balance > 0:
            for _tag, _feed_id, timestamp in reward_claimed_status:
                if balance > 0 and tag == _tag and feed_id == _feed_id:
                    if not reward_claimed_status[tag, feed_id, timestamp]:
                        balance -= details.reward
                        current_feeds[_, tag, feed_id][1] = max(balance, 0)
    return current_feeds
