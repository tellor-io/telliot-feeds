"""Example datafeed used by AMPLUSDVWAPReporter."""
from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.ampleforth.ampl_usd_vwap_query import AMPLUSDVWAP
from telliot_feeds.sources.ampl_usd_vwap import AMPLUSDVWAPSource


ampl_usd_vwap_feed = DataFeed(query=AMPLUSDVWAP(), source=AMPLUSDVWAPSource())
