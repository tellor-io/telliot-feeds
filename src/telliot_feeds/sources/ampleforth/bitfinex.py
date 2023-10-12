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
    for i in a_list:
        slot = (i[1] - start) // bucket_size
        amount = i[2]
        price = i[3]

        vwap_bucket = vwap_per_slot.get(slot)
        if vwap_bucket:
            vwap_bucket["trades"] += abs(amount * price)
            vwap_bucket["volume"] += abs(amount)
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
    if not all_trades:
        logger.warning(f"Could not get Bitfinex trades for {route}")
        return []

    if len(all_trades) >= 10000:
        logger.warning(f"Bitfinex response too big, scrolling: {route} ({start} - {end})")
        last_timestamp = all_trades[-1][1]
        next_frame = retrieve_bitfinex_trades(route, last_timestamp, end)
        all_trades.extend(next_frame)
    logger.info(f"Bitfinex trades for {route}: {len(all_trades)}")
    return all_trades


def calculate_all_single_via(symbol: dict[str, Any], start: int, end: int, show_debug: bool) -> dict[str, Any]:
    """Calculate VWAP for a single symbol via all exchanges."""
    from_list = retrieve_bitfinex_trades(SYMBOLS[symbol["hops"][0]]["bitFinexSymbol"], start, end)
    to_list = retrieve_bitfinex_trades(SYMBOLS[symbol["hops"][1]]["bitFinexSymbol"], start, end)
    result = {}

    if from_list and to_list:
        result[f"bitFinexVwapVia{symbol['via']}"] = volume_weighted_average_price(start, from_list, to_list)
    else:
        result[f"bitFinexVwapVia{symbol['via']}"] = NO_TRADES_FOUND  # type: ignore

    if show_debug:
        result["source"] = {}
        result["source"][f"bitFinex_{symbol['from']}to{symbol['via']}"] = [
            {"slot": slot, **bucket} for slot, bucket in build_buckets(start, from_list).items()
        ]
        result["source"][f"bitFinex_{symbol['via']}to{symbol['to']}"] = [
            {"slot": slot, **bucket} for slot, bucket in build_buckets(start, to_list).items()
        ]

    return result


def calculate_vwap_direct(symbol_route: dict[str, Any], start: int, end: int) -> dict[str, Any]:
    """Calculate VWAP for a single symbol directly."""
    response = retrieve_bitfinex_trades(symbol_route["bitFinexSymbol"], start, end)
    if len(response) == 0:
        raise Exception(f'No trades found for {symbol_route["bitFinexSymbol"]}')
    sum_amount_and_prices = sum([abs(trade[2] * trade[3]) for trade in response])
    sum_volume = sum([abs(trade[2]) for trade in response])
    return {"vwap": sum_amount_and_prices / sum_volume, "volume": sum_volume}


def calculate_vwap_via_all(symbol: dict[str, Any], start: int, end: int, show_debug: bool) -> dict[str, Any]:
    """Calculate VWAP for a single symbol via all symbols."""
    p_result = [calculate_vwap_direct(SYMBOLS[symbol["direct"]], start, end)]
    for h in symbol["viaHops"]:
        p_result.append(calculate_all_single_via(SYMBOLS[h], start, end, show_debug))
    result = {"bitFinexVwapDirect": p_result[0]}

    if show_debug:
        result["source"] = {}

    for i in range(1, len(p_result)):
        if show_debug and "source" in p_result[i]:
            source = p_result[i]["source"]
            del p_result[i]["source"]
            result["source"].update(source)
        result.update(p_result[i])

    all_vwaps = [
        v["vwap"] * v["volume"] for k, v in result.items() if k != "source" and v != NO_TRADES_FOUND  # type: ignore
    ]
    sum_volumes_and_prices = sum(all_vwaps)
    sum_volume = sum(v["volume"] for k, v in result.items() if k != "source" and "volume" in v)

    result["overall_vwap"] = sum_volumes_and_prices / sum_volume
    return result


async def get_value_from_bitfinex(symbol: dict[str, Any], start: int, end: int, show_debug: bool) -> dict[str, Any]:
    """Get VWAP for any symbol or group of symbols in SYMBOLS."""
    result = calculate_vwap_via_all(symbol, start, end, show_debug)
    return result


def main() -> None:
    """Main function."""
    # get ampl vwap
    # current_ts = int(time.time()) * 1000
    # ts_24hr_ago = current_ts - 86400000
    current_ts = 1675382399000
    ts_24hr_ago = 1675296000000
    result = asyncio.run(get_value_from_bitfinex(SYMBOLS["AMPL_USD_via_ALL"], ts_24hr_ago, current_ts, True))
    print(result["overall_vwap"])


if __name__ == "__main__":
    main()
