import asyncio
import csv

from telliot_feed_examples.sources.price.historical.kraken import (
    KrakenHistoricalPriceService,
)


def get_trades():
    six_hours = 60 * 60 * 6 # seconds
    trades, _ = asyncio.run(KrakenHistoricalPriceService().get_trades(
        "eth",
        "usd",
        period=six_hours,
        ts=1647782323,
    ))
    print("# trades in six hour window:", len(trades))
    return trades


def generate_csv(trades: list) -> None:
    # source: https://docs.kraken.com/rest/#operation/getRecentTrades
    cols = ["price", "volume", "time", "buy/sell", "market/limit", "miscellaneous"]
    
    with open('kraken_eth_usd_historical_price_source.csv', 'w') as f:
        write = csv.writer(f)
        write.writerow(cols)
        write.writerows(trades)


def main():
    trades = get_trades()
    generate_csv(trades)


if __name__ == "__main__":
    main()
