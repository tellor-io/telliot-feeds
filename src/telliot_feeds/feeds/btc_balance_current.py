"""Datafeed for BTC balance of an address at a specific timestamp."""
from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.btc_balance_current import BTCBalanceCurrent
from telliot_feeds.sources.btc_balance_current import BTCBalanceCurrentSource


btcAddress = None

btc_balance_current_feed = DataFeed(
    source=BTCBalanceCurrentSource(),
    query=BTCBalanceCurrent(btcAddress=btcAddress),
)

btcAddressEx = "bc1q06ywseed6sc3x2fafppchefqq8v9cqd0l6vx03"
btc_balance_current_feed_example = DataFeed(
    source=BTCBalanceCurrentSource(btcAddress=btcAddressEx),
    query=BTCBalanceCurrent(btcAddress=btcAddressEx),
)
