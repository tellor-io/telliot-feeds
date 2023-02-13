from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.evm_call import EVMCall
from telliot_feeds.sources.evm_call import EVMCallSource

evm_call_feed = DataFeed(
    query=EVMCall(),
    source=EVMCallSource(),
)

chain_id = 1
contract_address = "0x88dF592F8eb5D7Bd38bFeF7dEb0fBc02cf3778a0"
calldata = b"\x18\x16\x0d\xdd"
evm_call_feed_example = DataFeed(
    query=EVMCall(
        chainId=chain_id,
        contractAddress=contract_address,
        calldata=calldata,
    ),
    source=EVMCallSource(
        chainId=chain_id,
        contractAddress=contract_address,
        calldata=calldata,
    ),
)
