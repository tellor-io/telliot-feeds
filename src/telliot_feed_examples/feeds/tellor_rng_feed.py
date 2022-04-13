"""Datafeed for pseudorandom number from hashing multiple blockhashes together."""
from telliot_core.datafeed import DataFeed
from telliot_core.queries.tellor_rng import TellorRNG
from telliot_feed_examples.sources.blockhash_aggregator import TellorRNGManualSource

local_source = TellorRNGManualSource()

tellor_rng_feed = DataFeed(
    source=local_source,
    query=TellorRNG(timestamp=local_source.timestamp)
)
