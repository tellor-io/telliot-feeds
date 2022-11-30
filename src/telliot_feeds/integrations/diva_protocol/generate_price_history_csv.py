# type: ignore
import asyncio
import csv
from typing import Any

from telliot_feeds.sources.price.historical.cryptowatch import (
    CryptowatchHistoricalPriceService,
)
from telliot_feeds.sources.price.historical.kraken import (
    KrakenHistoricalPriceService,
)
from telliot_feeds.sources.price.historical.poloniex import (
    PoloniexHistoricalPriceService,
)


def print_num_trades(service_name: str, asset: str, currency: str, data: list[Any]) -> None:
    print(
        f"{service_name}: # trades in six hour window for {asset}/{currency}:",
        len(data),
    )


def get_kraken_data(period: int, ts: int, asset: str, currency: str) -> list:
    trades, _ = asyncio.run(
        KrakenHistoricalPriceService().get_trades(
            asset,
            currency,
            period=period,
            ts=ts,
        )
    )
    print_num_trades("Kraken", asset, currency, trades)
    return trades


def get_poloniex_data(period: int, ts: int, asset: str, currency: str) -> list:
    trades, _ = asyncio.run(PoloniexHistoricalPriceService().get_trades(asset, currency, period, ts))
    print_num_trades("Poloniex", asset, currency, trades)
    field_idx_lookup = {
        "globalTradeID": 0,
        "tradeID": 1,
        "date": 2,
        "type": 3,
        "rate": 4,
        "amount": 5,
        "total": 6,
        "orderNumber": 7,
    }
    trades_lists = []
    for trade in trades:
        new_trade = [0, 0, 0, 0, 0, 0, 0, 0]
        for key in trade.keys():
            new_trade[field_idx_lookup[key]] = trade[key]
        trades_lists.append(new_trade)
    return trades_lists


def get_cryptowatch_data(period: int, ts: int, asset: str, currency: str) -> list:
    candles, _ = asyncio.run(
        CryptowatchHistoricalPriceService().get_candles(
            asset=asset, currency=currency, period=period, candle_periods=60, ts=ts
        )
    )
    print(
        f"Cryptowatch: # candles in six hour window for {asset}/{currency}:",
        len(candles),
    )
    return candles


def generate_csv(file_name: str, data: list, cols: list) -> None:
    with open(file_name, "w") as f:
        write = csv.writer(f)
        write.writerow(cols)
        write.writerows(data)


def main():
    time_period = 60 * 60 * 6  # Six hours in seconds
    timestamp = 1648567107

    # Kraken historical price data
    # source: https://docs.kraken.com/rest/#operation/getRecentTrades
    cols = ["price", "volume", "time", "buy/sell", "market/limit", "miscellaneous"]

    data = get_kraken_data(ts=timestamp, period=time_period, asset="eth", currency="usd")
    generate_csv("kraken_eth_usd_historical_price_source.csv", data, cols)

    data = get_kraken_data(ts=timestamp, period=time_period, asset="xbt", currency="usd")
    generate_csv("kraken_xbt_usd_historical_price_source.csv", data, cols)

    # Poloniex historical price data
    # source: https://docs.poloniex.com/#returntradehistory-public
    cols = [
        "globalTradeID",
        "tradeID",
        "date",
        "type",
        "rate",
        "amount",
        "total",
        "orderNumber",
    ]

    data = get_poloniex_data(ts=timestamp, period=time_period, asset="eth", currency="tusd")
    generate_csv("poloniex_eth_tusd_historical_price_source.csv", data, cols)

    data = get_poloniex_data(ts=timestamp, period=time_period, asset="btc", currency="tusd")
    generate_csv("poloniex_btc_tusd_historical_price_source.csv", data, cols)

    # Cryptowatch historical price data
    # source:
    # cols = ["price", "volume", "time", "buy/sell", "market/limit", "miscellaneous"]
    cols = [
        "CloseTime",
        "OpenPrice",
        "HighPrice",
        "LowPrice",
        "ClosePrice",
        "Volume",
        "QuoteVolume",
    ]
    data = get_cryptowatch_data(ts=timestamp, period=time_period, asset="eth", currency="usd")
    generate_csv("cryptowatch_eth_usd_historical_price_source.csv", data, cols)
    data = get_cryptowatch_data(ts=timestamp, period=time_period, asset="btc", currency="usd")
    generate_csv("cryptowatch_btc_usd_historical_price_source.csv", data, cols)


if __name__ == "__main__":
    main()
