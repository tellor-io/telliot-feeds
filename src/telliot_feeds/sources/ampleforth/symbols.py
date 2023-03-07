"""
Get all bitfinex symbols: https://api.bitfinex.com/v2/conf/pub:list:pair:exchange
"""
from typing import Any


SYMBOLS: dict[str, Any] = {
    "AMPL_USD": {
        "bitFinexSymbol": "tAMPUSD",
    },
    "AMPL_BTC": {"bitFinexSymbol": "tAMPBTC", "kucoinSymbol": "AMPL-BTC"},
    "AMPL_UST": {"bitFinexSymbol": "tAMPUST", "kucoinSymbol": "AMPL-USDT"},
    "UST_USD": {
        "bitFinexSymbol": "tUSTUSD",
    },
    "BTC_USD": {
        "bitFinexSymbol": "tBTCUSD",
    },
    "AMPL_USD_via_UST": {
        "hops": ["AMPL_UST", "UST_USD"],
        "direct": "AMPL_USD",
        "from": "AMPL",
        "to": "USD",
        "via": "UST",
    },
    "AMPL_USD_via_BTC": {
        "hops": ["AMPL_BTC", "BTC_USD"],
        "direct": "AMPL_USD",
        "from": "AMPL",
        "to": "USD",
        "via": "BTC",
    },
    "AMPL_USD_via_ALL": {
        "viaHops": [
            "AMPL_USD_via_UST",
            "AMPL_USD_via_BTC",
        ],
        "direct": "AMPL_USD",
        "from": "AMPL",
        "to": "USD",
        "via": "ALL",
    },
}
