"""Datafeed for balance of an evm chain address at a specific timestamp."""
from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.evm_balance_current import EVMBalanceCurrent
from telliot_feeds.sources.evm_balance_current import EVMBalanceCurrentSource

chain_id = None
evm_address = None

evm_balance_current_feed = DataFeed(
    source=EVMBalanceCurrentSource(chainId=chain_id, evmAddress=evm_address),
    query=EVMBalanceCurrent(chainId=chain_id, evmAddress=evm_address),
)

chain_id_ex = 11155111
evm_address_ex = "0x210766226c54CDD6bD0401749D43E7a5585e3868"
evm_balance_current_feed_example = DataFeed(
    source=EVMBalanceCurrentSource(chainId=chain_id_ex, evmAddress=evm_address_ex),
    query=EVMBalanceCurrent(chainId=chain_id_ex, evmAddress=evm_address_ex),
)
