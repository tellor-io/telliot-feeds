"""Helper functions for reporting data for Diva Protocol."""
from telliot_core.api import DataFeed
from telliot_core.queries.diva_protocol import divaProtocolPolygon

from telliot_feed_examples.feeds.btc_usd_feed import btc_usd_median_feed
from telliot_feed_examples.feeds.eth_usd_feed import eth_usd_median_feed


DATAFEED_LOOKUP = {
    "ETH/USD": eth_usd_median_feed,
    "BTC/USD": btc_usd_median_feed,
}


def fetch_diva_datafeed(pool_id: int) -> DataFeed[float]:
    """Returns datafeed using user input option ID and corresponding
    asset information."""
    # TODO get asset from diva based on pool_id
    asset = "ETH/USD"
    feed = DATAFEED_LOOKUP[asset]
    feed.query = divaProtocolPolygon(pool_id)
    return feed
