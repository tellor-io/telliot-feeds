"""Bitfinex data source."""
import asyncio
import logging
from typing import Any

import requests

from telliot_feeds.sources.ampleforth.symbols import SYMBOLS

# import time


logger = logging.getLogger(__name__)


THOUSAND_MIN = 1000 * 60  # original JS names this variable "TEN_MINUTES"
NO_TRADES_FOUND = "No trades found"


def build_buckets(start: int, a_list: list[list[int]], bucket_size: int = THOUSAND_MIN) -> dict[int, dict[str, Any]]:
    """Build buckets for VWAP calculation."""
    vwap_per_slot: dict[int, dict[str, Any]] = {}
    print(a_list)
    for i in a_list:
        slot = (i[1] - start) // bucket_size
        amount = i[2]
        price = i[3]

        vwap_bucket = vwap_per_slot.get(slot)
        if vwap_bucket:
            vwap_bucket["trades"] = vwap_bucket["trades"] + abs(amount * price)
            vwap_bucket["volume"] = vwap_bucket["volume"] + abs(amount)
        else:
            vwap_bucket = {"timestamp": i[1], "trades": abs(amount * price), "volume": abs(amount)}
            vwap_per_slot[slot] = vwap_bucket

    for vwap_bucket in vwap_per_slot.values():
        if vwap_bucket["trades"] == 0 or vwap_bucket["volume"] == 0:
            vwap_bucket["vwap"] = 0
        else:
            vwap_bucket["vwap"] = vwap_bucket["trades"] / vwap_bucket["volume"]

    return vwap_per_slot


def merge_as_list(from_map: dict[int, dict[str, Any]], to_map: dict[int, dict[str, Any]]) -> list[dict[str, Any]]:
    """Merge two maps into a list of trades."""
    merged: list[dict[str, Any]] = []
    for slot, from_slot in from_map.items():
        s = slot
        to_slot = None
        while not to_slot:
            if s < 0:
                break
            to_slot = to_map.get(s)
            s = s - 1
        if to_slot:
            merged.append(
                {
                    "trades": abs((to_slot["vwap"] * from_slot["vwap"]) * from_slot["volume"]),
                    "volume": from_slot["volume"],
                }
            )
    return merged


def volume_weighted_average_price(start: int, from_list: list[list[int]], to_list: list[list[int]]) -> dict[str, Any]:
    """Calculate volume weighted average price."""
    from_map = build_buckets(start, from_list)
    to_map = build_buckets(start, to_list)
    merged_list = merge_as_list(from_map, to_map)
    sum_amount_and_prices = sum([m["trades"] for m in merged_list])
    sum_volume = sum([m["volume"] for m in merged_list])
    return {"vwap": sum_amount_and_prices / sum_volume, "volume": sum_volume}


def retrieve_bitfinex_trades(route: str, start: int, end: int) -> Any:
    """Retrieve trades from Bitfinex API."""
    # rate-limit: 30 req/min
    url = f"https://api-pub.bitfinex.com/v2/trades/{route}/hist?limit=10000&sort=1&start={start}&end={end}"
    try:
        response = requests.get(url)
    except Exception as e:
        logger.error(f"Error when retrieving Bitfinex trades for {route}:", e)
        return []

    # convert response
    all_trades = response.json()
    print(f"Bitfinex trades for {route}: {len(all_trades)}")
    if not all_trades:
        logger.warning(f"Could not get Bitfinex trades for {route}")
        return []

    if len(all_trades) >= 10000:
        logger.warn(f"Bitfinex response too big, scrolling: {route} ({start} - {end})")
        last_timestamp = all_trades[len(all_trades) - 1][1]
        next_frame = retrieve_bitfinex_trades(route, last_timestamp, end)
        all_trades = all_trades.concat(next_frame)

    return all_trades


def calculate_bitfinex_single_via(symbol: dict[str, Any], start: int, end: int, show_debug: bool) -> Any:
    """Calculate VWAP for a single symbol via Bitfinex."""
    from_list = retrieve_bitfinex_trades(symbol["hops"][0], start, end)
    to_list = retrieve_bitfinex_trades(symbol["hops"][1], start, end)
    if len(from_list) == 0 or len(to_list) == 0:
        result = {}
        result[f'bitFinexVwapVia{symbol["via"]}'] = NO_TRADES_FOUND
        return result

    vwap = volume_weighted_average_price(start, from_list, to_list)

    result = {"vwap": vwap["vwap"]}
    result[f'bitFinexVwapVia{symbol["via"]}'] = vwap["vwap"]
    if show_debug:
        result["source"] = {}  # type: ignore
        result["source"][f'bitFinexRawData_{symbol["from"]}to{symbol["via"]}'] = build_buckets(  # type: ignore
            start, from_list
        )
        result["source"][f'bitFinexRawData_{symbol["via"]}to{symbol["to"]}'] = build_buckets(  # type: ignore
            start, to_list
        )
    return result


def calculate_all_single_via(symbol: dict[str, Any], start: int, end: int, show_debug: bool) -> dict[str, Any]:
    """Calculate VWAP for a single symbol via all exchanges."""
    from_list = retrieve_bitfinex_trades(symbol["hops"][0], start, end)
    to_list = retrieve_bitfinex_trades(symbol["hops"][1], start, end)
    if len(from_list) == 0 or len(to_list) == 0:
        result = {}
        result[f'bitFinexVwapVia{symbol["via"]}'] = NO_TRADES_FOUND
        return result

    vwap = volume_weighted_average_price(start, from_list, to_list)

    result = {"vwap": vwap["vwap"]}
    result[f'bitFinexVwapVia{symbol["via"]}'] = vwap["vwap"]
    if show_debug:
        result["source"] = {}  # type: ignore
        result["source"][f'bitFinexRawData_{symbol["from"]}to{symbol["via"]}'] = build_buckets(  # type: ignore
            start, from_list
        )
        result["source"][f'bitFinexRawData_{symbol["via"]}to{symbol["to"]}'] = build_buckets(  # type: ignore
            start, to_list
        )
    return result


def calculate_vwap_direct(symbol_route: dict[str, Any], start: int, end: int) -> dict[str, Any]:
    """Calculate VWAP for a single symbol directly."""
    response = retrieve_bitfinex_trades(symbol_route["bitFinexSymbol"], start, end)
    if len(response) == 0:
        raise Exception(f'No trades found for {symbol_route["bitFinexSymbol"]}')
    sum_amount_and_prices = sum([trade[2] * trade[3] for trade in response])
    sum_volume = sum([trade[2] for trade in response])
    return {"vwap": sum_amount_and_prices / sum_volume, "volume": sum_volume}


def calculate_vwap_via(symbol: dict[str, Any], start: int, end: int, show_debug: bool) -> dict[str, Any]:
    """Calculate VWAP for a single symbol via another symbol."""
    vwap_direct = calculate_vwap_direct(symbol["direct"], start, end)
    via_result = calculate_bitfinex_single_via(symbol, start, end, show_debug)

    result = {"vwapDirect": vwap_direct["vwap"]}
    if via_result["vwap"]:
        result["mean"] = (vwap_direct["vwap"] + via_result["vwap"]) / 2
    del via_result["vwap"]
    result.update(via_result)
    return result


def calculate_vwap_via_all(symbol: dict[str, Any], start: int, end: int, show_debug: bool) -> dict[str, Any]:
    """Calculate VWAP for a single symbol via all symbols."""
    p_result = [calculate_vwap_direct(SYMBOLS[symbol["direct"]], start, end)]  # type: ignore
    for h in symbol["viaHops"]:
        p_result.append(calculate_all_single_via(SYMBOLS[h], start, end, show_debug))  # type: ignore
    result = {"bitFinexVwapDirect": p_result[0]}

    if show_debug:
        result["source"] = {}

    for i in range(1, len(p_result)):
        if show_debug and "source" in p_result[i]:
            source = p_result[i]["source"]
            del p_result[i]["source"]
            result["source"].update(source)
        result.update(p_result[i])
    all_vwaps = [v[1] for v in result.items() if v[0] != "source" and v[1] != NO_TRADES_FOUND]  # type: ignore

    sum_amount_and_prices = sum([m["vwap"] * m["volume"] for m in all_vwaps])
    sum_volume = sum([m["volume"] for m in all_vwaps])

    result["overall_vwap"] = sum_amount_and_prices / sum_volume
    return result


async def get_value_from_bitfinex(symbol: dict[str, Any], start: int, end: int, show_debug: bool) -> dict[str, Any]:
    """Get VWAP for any symbol or group of symbols in SYMBOLS."""
    if "direct" not in symbol:
        result = calculate_vwap_direct(symbol, start, end)
    elif "viaHops" in symbol:
        result = calculate_vwap_via_all(symbol, start, end, show_debug)
    else:
        result = calculate_vwap_via(symbol, start, end, show_debug)
    return result


def main() -> None:
    """Main function."""
    # get ampl vwap
    # current_ts = int(time.time()) * 1000
    # ts_24hr_ago = current_ts - 86400000
    current_ts = 1675382399000
    ts_24hr_ago = 1675296000000
    result = asyncio.run(
        get_value_from_bitfinex(SYMBOLS["AMPL_USD_via_ALL"], ts_24hr_ago, current_ts, True)  # type: ignore
    )
    print(result)


if __name__ == "__main__":
    main()
