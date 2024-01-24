"""Datafeed for BTC balance of an address at a specific timestamp."""
from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.btc_balance import BTCBalance
from telliot_feeds.sources.btc_balance import BTCBalanceSource

bitcoin_balance_feed = DataFeed(
    source=BTCBalanceSource(),
    query=BTCBalance(),
)


btcAddress = "bc1q06ywseed6sc3x2fafppchefqq8v9cqd0l6vx03"
timestamp = 1706051389
btc_balance_feed_example = DataFeed(
    source=BTCBalanceSource(address=btcAddress, timestamp=timestamp),
    query=BTCBalance(btcAddress == btcAddress, timestamp=timestamp),
)
