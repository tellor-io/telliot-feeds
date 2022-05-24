"""Datafeed for reporting responses to the Morphware query type.

More info: """
from telliot_core.datafeed import DataFeed
from telliot_core.queries.morphware import Morphware
from telliot_core.sources.morphware import MorphwareV1Source


morphware_v1_feed = DataFeed(query=Morphware(version=1), source=MorphwareV1Source())
