"""
Datafeed for reporting responses to the Snapshot query type.

More info:
https://github.com/tellor-io/dataSpecs/blob/main/types/Snapshot.md

"""
from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.snapshot import Snapshot
from telliot_feeds.sources.manual_input_source import ManualSnapshotInputSource

proposalId = None

snapshot_manual_feed = DataFeed(
    query=Snapshot(proposalId=proposalId),
    source=ManualSnapshotInputSource(),
)
