"""
Datafeed for reporting responses to the Snapshot query type.

More info:
https://github.com/tellor-io/dataSpecs/blob/main/types/Snapshot.md

"""
from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.snapshot import Snapshot
from telliot_feeds.sources.manual.snapshot import ManualSnapshotInputSource

proposalId = None

snapshot_manual_feed = DataFeed(
    query=Snapshot(proposalId=proposalId),
    source=ManualSnapshotInputSource(),
)
snapshot_feed_example = DataFeed(
    query=Snapshot(proposalId="cce9760adea906176940ae5fd05bc007cc9252b524832065800635484cb5cb57"),
    source=ManualSnapshotInputSource(),
)
