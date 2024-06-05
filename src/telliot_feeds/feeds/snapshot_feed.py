"""
Datafeed for reporting responses to the Snapshot query type.

More info:
https://github.com/tellor-io/dataSpecs/blob/main/types/Snapshot.md

"""
from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.snapshot import Snapshot
from telliot_feeds.sources.manual.snapshot import ManualSnapshotInputSource

proposalId = None
transactionsHash = None
moduleAddress = None

snapshot_manual_feed = DataFeed(
    query=Snapshot(proposalId=proposalId, transactionsHash=transactionsHash, moduleAddress=moduleAddress),
    source=ManualSnapshotInputSource(),
)
snapshot_feed_example = DataFeed(
    query=Snapshot(
        proposalId="cce9760adea906176940ae5fd05bc007cc9252b524832065800635484cb5cb57",
        transactionsHash="0x6f49a2f0da92ef653ba883aa21b2e3ff4d3350080b5627db6eba68b45eae1fd7",
        moduleAddress="0xB1bB6479160317a41df61b15aDC2d894D71B63D9",
    ),
    source=ManualSnapshotInputSource(),
)
