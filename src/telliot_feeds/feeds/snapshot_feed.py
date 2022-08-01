"""
Datafeed for reporting responses to the GasPriceOracle query type.

More info:
https://github.com/tellor-io/dataSpecs/blob/main/types/GasPriceOracle.md

"""
from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.snapshot import Snapshot
from telliot_feeds.sources.manual_input_source import ManualSnapshotInputSource

proposalId = ""

snapshot_feed = DataFeed(
    query=Snapshot(proposalId=proposalId),
    source=ManualSnapshotInputSource(),
)
