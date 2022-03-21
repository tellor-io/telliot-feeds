import asyncio
import csv

from telliot_feed_examples.sources.price.historical.kraken import (
    KrakenHistoricalPriceService,
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
    print("# trades in six hour window:", len(trades))
    return trades


def get_poloniex_data(period: int, ts: int, asset: str, currency: str) -> list:
    pass


def get_cryptowatch_data(period: int, ts: int, asset: str, currency: str) -> list:
    pass


def generate_csv(file_name: str, data: list, cols: list) -> None:
    with open(file_name, "w") as f:
        write = csv.writer(f)
        write.writerow(cols)
        write.writerows(data)


def main():
    time_period = 60 * 60 * 6  # Six hours in seconds
    timestamp = 1647782323

    # Kraken historical price data
    # source: https://docs.kraken.com/rest/#operation/getRecentTrades
    cols = ["price", "volume", "time", "buy/sell", "market/limit", "miscellaneous"]

    data = get_kraken_data(
        ts=timestamp, period=time_period, asset="eth", currency="usd"
    )
    generate_csv("kraken_eth_usd_historical_price_source.csv", data, cols)

    data = get_kraken_data(
        ts=timestamp, period=time_period, asset="xbt", currency="usd"
    )
    generate_csv("kraken_xbt_usd_historical_price_source.csv", data, cols)

    # Poloniex historical price data
    # source:
    cols = ["price", "volume", "time", "buy/sell", "market/limit", "miscellaneous"]
    # data = get_poloniex_data()
    # generate_csv("kraken_eth_usd_historical_price_source.csv", data, cols)

    # Cryptowatch historical price data
    # source:
    cols = ["price", "volume", "time", "buy/sell", "market/limit", "miscellaneous"]
    # data = get_cryptowatch_data()
    # generate_csv("kraken_eth_usd_historical_price_source.csv", data, cols)


if __name__ == "__main__":
    main()
