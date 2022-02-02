"""Helper functions for reporting data for Diva Protocol."""
from telliot_core.queries.diva_protocol import divaProtocolPolygon
from telliot_feed_examples.feeds.eth_usd_feed import eth_usd_median_feed
from telliot_core.api import DataFeed


def fetch_diva_datafeed(option_id: int) -> DataFeed[float]:
    """Returns datafeed using user input option ID and corresponding
    asset information."""
    # TODO get feed based on asset
    feed = eth_usd_median_feed
    feed.query = divaProtocolPolygon(option_id)
    return feed
