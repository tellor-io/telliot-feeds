"""Example datafeed used by AMPLUSDVWAPReporter."""
from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.legacy_query import LegacyRequest
from telliot_feeds.sources.ampl_usd_vwap import AMPLUSDVWAPSource


ampl_usd_vwap_feed = DataFeed(query=LegacyRequest(legacy_id=10), source=AMPLUSDVWAPSource())
