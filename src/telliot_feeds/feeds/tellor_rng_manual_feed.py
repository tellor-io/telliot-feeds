from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.tellor_rng import TellorRNG
from telliot_feeds.sources.manual.tellor_rng_manual_source import TellorRNGManualInputSource


timestamp = None

tellor_rng_manual_feed = DataFeed(
    query=TellorRNG(timestamp=timestamp), source=TellorRNGManualInputSource()  # type: ignore
)
