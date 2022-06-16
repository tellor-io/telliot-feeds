"""Datafeed for reporting responses to the Morphware query type.

More info: """
from telliot_feed_examples.datafeed import DataFeed
from telliot_feed_examples.queries.morphware import Morphware

from telliot_feed_examples.sources.morphware import MorphwareV1Source


morphware_v1_feed = DataFeed(query=Morphware(version=1), source=MorphwareV1Source())
