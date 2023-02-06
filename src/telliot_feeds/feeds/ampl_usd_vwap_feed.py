"""Example datafeed used by AmpleforthCustomSpotPriceReporter."""
from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.ampleforth.ampl_usd_vwap import AmpleforthCustomSpotPrice
from telliot_feeds.sources.ampleforth.ampl_usd_vwap import AmpleforthCustomSpotPriceSource


ampl_usd_vwap_feed = DataFeed(query=AmpleforthCustomSpotPrice(), source=AmpleforthCustomSpotPriceSource())
