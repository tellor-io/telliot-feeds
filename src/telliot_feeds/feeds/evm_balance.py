"""Datafeed for balance of an evm chain address at a specific timestamp."""
from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.evm_balance import EVMBalance
from telliot_feeds.sources.evm_balance import EVMBalanceSource

chain_id = None
evm_address = None
timestamp = None

evm_balance_feed = DataFeed(
    source=EVMBalanceSource(),
    query=EVMBalance(chainId=chain_id, evmAddress=evm_address, timestamp=timestamp),
)

chain_id_ex = 11155111
evm_address_ex = "0x210766226c54CDD6bD0401749D43E7a5585e3868"
timestamp_ex = 1706302197
evm_balance_feed_example = DataFeed(
    source=EVMBalanceSource(chainId=chain_id_ex, evmAddress=evm_address_ex, timestamp=timestamp_ex),
    query=EVMBalance(chainId=chain_id_ex, evmAddress=evm_address_ex, timestamp=timestamp_ex),
)
