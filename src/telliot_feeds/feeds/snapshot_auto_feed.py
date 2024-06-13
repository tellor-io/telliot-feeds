"""Datafeed for automatic Snapshot proposal result."""
from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.snapshot_auto_query import SnapshotAuto
from telliot_feeds.sources.snapshot_result_source import SnapshotVoteResultSource

proposal_id = None
transactions_hash = None
module_address = None

snapshot_auto_feed = DataFeed(
    query=SnapshotAuto(proposal_id=proposal_id, transactions_hash=transactions_hash, module_address=module_address),
    source=SnapshotVoteResultSource(
        proposalId=proposal_id, transactionsHash=transactions_hash, moduleAddress=module_address
    ),
)

proposalId = "0xe992735684706baf15e447b537acbaaac8ef74d8ce0033205456ceed58bffdf6"
transactionsHash = "0xfd471b205457d8bac0d29a63292545f9f3189086a31a7794de341d55e9f50188"
moduleAddress = "0xB1bB6479160317a41df61b15aDC2d894D71B63D9"
snapshot_auto_feed_example = DataFeed(
    source=SnapshotVoteResultSource(
        proposalId=proposalId, transactionsHash=transactionsHash, moduleAddress=moduleAddress
    ),
    query=SnapshotAuto(proposal_id=proposalId, transactions_hash=transactionsHash, module_address=moduleAddress),
)
